import os
import re
import json
import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "processed", "corpus_chunks.jsonl"))
CHROMA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "chroma"))

RRF_K = 60  # standard Reciprocal Rank Fusion constant
CANDIDATES_PER_METHOD = 20  # results each method contributes before fusion

articles = []
with open(CORPUS_PATH, encoding="utf-8") as f:
    for line in f:
        articles.append(json.loads(line))
articles_by_number = {a["article_number"]: a for a in articles}

# --- Lexical index (BM25) ---
def tokenize(text):
    # \w is unicode-aware, so accented French words (é, à, ç...) tokenize
    # correctly without any extra configuration.
    return re.findall(r"\w+", text.lower())


bm25_corpus = [tokenize(a["article_text"]) for a in articles]
bm25_index = BM25Okapi(bm25_corpus)
bm25_ids = [a["article_number"] for a in articles]  # same order as bm25_corpus

# --- Dense index (already built into data/chroma by database.py) ---
embed_model = SentenceTransformer("BAAI/bge-m3")
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection("code_du_travail")


def bm25_search(query, k=CANDIDATES_PER_METHOD):
    scores = bm25_index.get_scores(tokenize(query))
    ranked = sorted(zip(bm25_ids, scores), key=lambda pair: pair[1], reverse=True)
    return [article_id for article_id, score in ranked[:k]]


def dense_search(query, k=CANDIDATES_PER_METHOD):
    query_embedding = embed_model.encode([query], normalize_embeddings=True).tolist()
    result = collection.query(query_embeddings=query_embedding, n_results=k)
    return result["ids"][0]


def hybrid_search(query, k=5):
    """Reciprocal Rank Fusion of dense + lexical results.

    Each method contributes 1/(RRF_K + rank) per article based on its RANK in
    that method's result list, not its raw score -- this sidesteps having to
    normalize BM25 scores (unbounded) against cosine similarities (0-1) onto
    the same scale, which is the usual pain point of combining the two.
    """
    dense_ids = dense_search(query)
    lexical_ids = bm25_search(query)

    fused_scores = {}
    for ranked_ids in (dense_ids, lexical_ids):
        for rank, article_id in enumerate(ranked_ids):
            fused_scores[article_id] = fused_scores.get(article_id, 0.0) + 1.0 / (RRF_K + rank)

    top_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)[:k]
    return [articles_by_number[article_id] for article_id in top_ids]


if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "Quelle est la durée du congé annuel payé ?"
    print(f"Question: {question}\n")
    for article in hybrid_search(question):
        print(f"Article {article['article_number']} — {article['article_text'][:120]}...")
