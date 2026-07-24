import re

from retriever import retrieve
from generator import generate, DISCLAIMER

# Pre-LLM abstention gate: if the best semantic match is below this cosine
# similarity, the question is treated as clearly unrelated and the LLM is never
# called. Calibrated empirically (eval/run_eval.py, abstention section): on a
# BGE-M3 index, labor-law questions score ~0.62-0.68, purely non-legal ones
# (cooking, geography) ~0.33-0.35, and other legal domains (family, penal,
# commercial law) land in between at ~0.47-0.52 because they share legal French
# vocabulary. A single threshold therefore CANNOT separate labor law from other
# legal domains — and shouldn't try to: when the corpus is later extended to
# other codes, those questions should become answerable. So this gate only
# filters the clearly-unrelated band; legal-but-out-of-corpus questions pass
# through and are caught by the LLM's prompt-level abstention (it sees the
# retrieved articles don't answer the question). Tunable, not "final".
ABSTENTION_THRESHOLD = 0.42

ABSTENTION_MESSAGE = (
    "Je ne dispose pas d'information suffisante dans le corpus fourni "
    "(Code du travail, Loi 65-99) pour répondre à cette question."
)

# Matches "Article 152", "article 152", "(Article 152)" — used to check that
# every article the model cites was actually in the context we gave it.
CITATION_RE = re.compile(r"[Aa]rticle\s+(\d{1,3})")


def cited_article_numbers(answer):
    return set(CITATION_RE.findall(answer))


def answer_question(question, k=5, rerank=False):
    """Full RAG turn. Returns a structured result dict:

      abstained          -> bool (retrieval too weak, LLM not called)
      answer             -> the response text
      sources            -> list of retrieved article dicts
      cited              -> set of article numbers the answer cites
      unverified         -> cited numbers NOT present in sources (hallucinated)
      retrieval_score    -> best dense cosine similarity
      error              -> str if the LLM was unreachable, else None
    """
    result = retrieve(question, k=k, rerank=rerank)
    articles = result["articles"]
    score = result["top_similarity"]

    if score < ABSTENTION_THRESHOLD:
        return {
            "abstained": True,
            "answer": ABSTENTION_MESSAGE,
            "sources": articles,
            "cited": set(),
            "unverified": set(),
            "retrieval_score": score,
            "error": None,
        }

    answer, error = generate(question, articles)
    if error:
        return {
            "abstained": False,
            "answer": None,
            "sources": articles,
            "cited": set(),
            "unverified": set(),
            "retrieval_score": score,
            "error": error,
        }

    cited = cited_article_numbers(answer)
    retrieved_ids = {a["article_number"] for a in articles}
    unverified = cited - retrieved_ids  # cited but not in the provided context

    return {
        "abstained": False,
        "answer": answer,
        "sources": articles,
        "cited": cited,
        "unverified": unverified,
        "retrieval_score": score,
        "error": None,
    }


def _print_result(question, result):
    print(f"\nQuestion : {question}")
    print(f"[score de recherche : {result['retrieval_score']:.3f}]\n")

    if result["error"]:
        print(f"[!] {result['error']}")
        return

    print(result["answer"])

    if not result["abstained"]:
        if result["unverified"]:
            print(
                f"\n[!] Citations non vérifiées (absentes du contexte fourni) : "
                f"{', '.join(sorted(result['unverified']))}"
            )
        print("\n-- Articles retrouvés --")
        for a in result["sources"]:
            print(f"  Article {a['article_number']} · {a['titre'] or a['livre'] or ''}")

    print(f"\n{DISCLAIMER}")


if __name__ == "__main__":
    import sys

    # Windows consoles default to cp1252, which can't encode accented output or
    # symbols; force UTF-8 so the CLI never crashes on é/à/etc.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    question = " ".join(sys.argv[1:]) or "Quelle est la durée du congé annuel payé ?"
    _print_result(question, answer_question(question))
