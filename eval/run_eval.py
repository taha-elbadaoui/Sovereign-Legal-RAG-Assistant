"""Retrieval evaluation: compares dense-only, BM25-only and hybrid search on the
reference question set, and reports the abstention signal distribution.

Metrics (retrieval questions only — those with a gold article):
  Recall@k : fraction of questions where an expected article is in the top-k.
  MRR      : mean reciprocal rank of the first expected article (0 if absent).

Run from the repo root:  python eval/run_eval.py
No LLM needed — this measures retrieval quality only.
"""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from retriever import dense_search, bm25_search, retrieve  # noqa: E402

REF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference_qa.jsonl")
K = 5


def load_reference():
    with open(REF_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def dense_ids(query, k):
    return [article_id for article_id, _ in dense_search(query, k=k)]


def bm25_ids(query, k):
    return bm25_search(query, k=k)


def hybrid_ids(query, k):
    return [a["article_number"] for a in retrieve(query, k=k)["articles"]]


def first_hit_rank(ranked_ids, expected):
    for rank, article_id in enumerate(ranked_ids, start=1):
        if article_id in expected:
            return rank
    return None


def evaluate(method_fn, questions, k):
    hits, reciprocal_ranks = 0, []
    for q in questions:
        ranked = method_fn(q["question"], k)
        rank = first_hit_rank(ranked, set(q["expected_articles"]))
        if rank:
            hits += 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)
    recall = hits / len(questions)
    mrr = sum(reciprocal_ranks) / len(questions)
    return recall, mrr


def main():
    reference = load_reference()
    retrieval_qs = [q for q in reference if q["type"] == "retrieval"]
    abstention_qs = [q for q in reference if q["type"] == "abstention"]

    print(f"Jeu de référence : {len(retrieval_qs)} questions de recherche, "
          f"{len(abstention_qs)} questions d'abstention.\n")

    methods = {"Dense seul": dense_ids, "BM25 seul": bm25_ids, "Hybride (RRF)": hybrid_ids}

    print(f"--- Qualité de la recherche (k={K}) ---")
    print(f"{'Méthode':<18}{'Recall@' + str(K):>12}{'MRR':>10}")
    for name, fn in methods.items():
        recall, mrr = evaluate(fn, retrieval_qs, K)
        print(f"{name:<18}{recall:>12.3f}{mrr:>10.3f}")

    print(f"\n--- Signal d'abstention (similarité dense max) ---")
    in_scores = sorted(retrieve(q["question"])["top_similarity"] for q in retrieval_qs)
    out_scores = sorted(retrieve(q["question"])["top_similarity"] for q in abstention_qs)
    print(f"Questions dans le périmètre : min={in_scores[0]:.3f}  max={in_scores[-1]:.3f}")
    print(f"Questions hors périmètre    : min={out_scores[0]:.3f}  max={out_scores[-1]:.3f}")


if __name__ == "__main__":
    main()
