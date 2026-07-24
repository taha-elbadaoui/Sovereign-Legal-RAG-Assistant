import os
import re
import json
import numpy as np
import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "processed", "corpus_chunks.jsonl"))
CHROMA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "chroma"))

RRF_K = 60  # standard Reciprocal Rank Fusion constant
CANDIDATES_PER_METHOD = 20  # results each method contributes before fusion
RERANK_POOL = 10  # candidates handed to the cross-encoder when reranking is on

articles = []
with open(CORPUS_PATH, encoding="utf-8") as f:
    for line in f:
        articles.append(json.loads(line))
articles_by_number = {a["article_number"]: a for a in articles}


def tokenize(text):
    # \w is unicode-aware, so accented French words (é, à, ç...) tokenize
    # correctly without any extra configuration.
    return re.findall(r"\w+", text.lower())


bm25_corpus = [tokenize(a["article_text"]) for a in articles]
bm25_index = BM25Okapi(bm25_corpus)
bm25_ids = [a["article_number"] for a in articles]  # same order as bm25_corpus

# Reuses the index database.py already built into data/chroma.
embed_model = SentenceTransformer("BAAI/bge-m3")
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection("code_du_travail")

# Cross-encoder reranker is loaded lazily: it downloads ~2.3GB on first use, so
# the default pipeline (rerank off) never pays that cost.
_reranker = None


def _get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")
    return _reranker


def bm25_search(query, k=CANDIDATES_PER_METHOD):
    scores = bm25_index.get_scores(tokenize(query))
    ranked = sorted(zip(bm25_ids, scores), key=lambda pair: pair[1], reverse=True)
    return [article_id for article_id, score in ranked[:k]]


def dense_search(query, k=CANDIDATES_PER_METHOD):
    """Return [(article_id, cosine_similarity), ...], best first.

    Similarity is computed as the dot product between the (normalized) query
    embedding and each (normalized) stored embedding — so it is a true cosine
    in [-1, 1] regardless of the distance metric Chroma is configured with.
    """
    query_embedding = embed_model.encode([query], normalize_embeddings=True)
    result = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=k,
        include=["embeddings"],
    )
    ids = result["ids"][0]
    doc_embeddings = np.array(result["embeddings"][0])
    similarities = doc_embeddings @ query_embedding[0]
    return list(zip(ids, similarities.tolist()))


# Matches "article 32", "l'article 32", "Article premier" in the QUESTION
# itself (not the corpus) -- used to detect a direct-lookup request.
EXPLICIT_ARTICLE_RE = re.compile(r"[Aa]rticle\s+(premier|\d{1,3})")


def explicit_article_refs(query):
    """Article numbers the user names directly in their question, e.g.
    "Que dit l'article 32 ?" -> ["32"].

    Dense/lexical search both match the QUESTION's meaning against article
    BODY text -- but a meta-question like "what does article 32 say" shares
    no vocabulary with article 32's actual content (contract suspension,
    military service), so it can rank arbitrarily low or miss entirely even
    though the article is real and in the corpus. When a query names a real
    article number directly, that article is included unconditionally rather
    than left to compete on semantic/lexical similarity it was never going to
    win on.
    """
    refs = []
    for match in EXPLICIT_ARTICLE_RE.finditer(query):
        num = "1" if match.group(1) == "premier" else match.group(1)
        if num in articles_by_number and num not in refs:
            refs.append(num)
    return refs


def rerank_articles(query, candidate_articles):
    reranker = _get_reranker()
    pairs = [(query, a["article_text"]) for a in candidate_articles]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(candidate_articles, scores), key=lambda pair: pair[1], reverse=True)
    return [article for article, score in ranked]


def retrieve(query, k=5, rerank=False):
    """Full retrieval: dense + lexical, fused by RRF, optionally reranked.

    Returns a dict with:
      - articles: the top-k article dicts
      - top_similarity: best dense cosine similarity across all candidates,
        used as the pre-LLM abstention signal ("is anything even close?")
    """
    dense = dense_search(query)
    dense_ids = [article_id for article_id, _ in dense]
    lexical_ids = bm25_search(query)

    fused_scores = {}
    for ranked_ids in (dense_ids, lexical_ids):
        for rank, article_id in enumerate(ranked_ids):
            fused_scores[article_id] = fused_scores.get(article_id, 0.0) + 1.0 / (RRF_K + rank)

    # Directly-named articles always make the cut, ranked above anything
    # fusion scored (see explicit_article_refs for why fusion can't be
    # trusted for this case).
    for num in explicit_article_refs(query):
        fused_scores[num] = float("inf")

    pool = RERANK_POOL if rerank else k
    top_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)[:pool]
    result_articles = [articles_by_number[article_id] for article_id in top_ids]

    if rerank:
        result_articles = rerank_articles(query, result_articles)
    result_articles = result_articles[:k]

    top_similarity = max((sim for _, sim in dense), default=0.0)
    # A named article is, by definition, relevant -- don't let a low dense
    # score (expected here: the question and the article's own body text
    # share little vocabulary) trip the pre-LLM abstention gate in app.py.
    if explicit_article_refs(query):
        top_similarity = 1.0
    return {"articles": result_articles, "top_similarity": top_similarity}


def hybrid_search(query, k=5, rerank=False):
    """Thin wrapper returning just the article list."""
    return retrieve(query, k=k, rerank=rerank)["articles"]


if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "Quelle est la durée du congé annuel payé ?"
    result = retrieve(question)
    print(f"Question: {question}")
    print(f"Score de recherche (similarité max): {result['top_similarity']:.3f}\n")
    for article in result["articles"]:
        print(f"Article {article['article_number']} — {article['article_text'][:110]}...")
