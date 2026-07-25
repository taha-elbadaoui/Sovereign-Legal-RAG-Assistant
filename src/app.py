import re
import time

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

# Matches the article numbers a generated answer cites, so we can check each one
# was actually in the context we supplied.
#
# Handles the enumerated form the model actually produces -- "Articles 154 et 156",
# "les articles 53, 55 et 56" -- not just the singular case. An earlier version
# anchored on "[Aa]rticle\s+" and silently missed EVERY plural citation, which
# both weakened the F6 guardrail and made the measured citation rate too low.
#
# "\d{1,3}(?!\d)" refuses 4+ digit numbers on purpose: no article in this law
# exceeds 589, so "l'article 1098 du Code des obligations" (a cross-reference to
# a different code) must not be read as a citation of article 109.
CITATION_LEAD_RE = re.compile(
    r"[Aa]rticles?\s+(premier|\d{1,3}(?!\d))"      # first number after "article(s)"
    r"((?:\s*(?:,|et|and|&)\s*\d{1,3}(?!\d))*)"    # ", 55 et 56" continuation
)
NUMBER_RE = re.compile(r"\d{1,3}(?!\d)")


def cited_article_numbers(answer):
    found = set()
    for match in CITATION_LEAD_RE.finditer(answer):
        head = match.group(1)
        found.add("1" if head == "premier" else head)
        found.update(NUMBER_RE.findall(match.group(2) or ""))
    return found


def answer_question(question, k=5, rerank=False):
    """Full RAG turn. Returns a structured result dict:

      abstained          -> bool (retrieval too weak, LLM not called)
      answer             -> the response text
      sources            -> list of retrieved article dicts
      cited              -> set of article numbers the answer cites
      unverified         -> cited numbers NOT present in sources (hallucinated)
      retrieval_score    -> best dense cosine similarity
      timings            -> {"retrieval": s, "generation": s, "total": s}
                            generation is 0.0 when the gate abstained
      error              -> str if the LLM was unreachable, else None
    """
    started = time.perf_counter()
    result = retrieve(question, k=k, rerank=rerank)
    t_retrieval = time.perf_counter() - started
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
            "timings": {"retrieval": t_retrieval, "generation": 0.0, "total": t_retrieval},
            "error": None,
        }

    gen_started = time.perf_counter()
    answer, error = generate(question, articles)
    t_generation = time.perf_counter() - gen_started
    timings = {
        "retrieval": t_retrieval,
        "generation": t_generation,
        "total": t_retrieval + t_generation,
    }

    if error:
        return {
            "abstained": False,
            "answer": None,
            "sources": articles,
            "cited": set(),
            "unverified": set(),
            "retrieval_score": score,
            "timings": timings,
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
        "timings": timings,
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
