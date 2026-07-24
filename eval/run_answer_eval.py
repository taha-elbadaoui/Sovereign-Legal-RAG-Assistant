"""End-to-end answer evaluation -- the answer-side counterpart to run_eval.py.

run_eval.py measures RETRIEVAL only (critère 4 du plan : Recall@k, MRR) and
needs no LLM. This script exercises the full pipeline through the local model
to measure the criteria that depend on the generated answer:

  Critère 2 — Citation systématique : part des réponses (hors abstention)
              qui citent au moins un numéro d'article.
  Critère 3 — Abstention correcte  : part des questions hors périmètre pour
              lesquelles le système s'abstient effectivement.
  Critère 5 — Vérification des citations : part des articles cités qui
              figuraient réellement dans le contexte fourni.

Plus, en bonus, la justesse de la source : l'article attendu figure-t-il
parmi ceux réellement cités par la réponse (et pas seulement retrouvés) ?

Run from the repo root:  python eval/run_answer_eval.py
Requires Ollama running. Comptez ~10 s par question.
"""
import os
import sys
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from app import answer_question, ABSTENTION_MESSAGE  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference_qa.jsonl")
REPORT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultats-evaluation.md")

# An answer counts as an abstention if the model produced the exact refusal
# sentence from the system prompt, or the pre-LLM gate fired.
ABSTENTION_MARKERS = [
    "je ne dispose pas d'information suffisante",
    "ne dispose pas d'information suffisante",
]


def is_abstention(result):
    if result["abstained"]:
        return True
    text = (result["answer"] or "").lower()
    return any(marker in text for marker in ABSTENTION_MARKERS)


def main():
    with open(REF_PATH, encoding="utf-8") as f:
        reference = [json.loads(line) for line in f]

    retrieval_qs = [q for q in reference if q["type"] == "retrieval"]
    abstention_qs = [q for q in reference if q["type"] == "abstention"]

    rows = []
    started = time.time()

    for i, q in enumerate(reference, 1):
        print(f"[{i}/{len(reference)}] {q['question'][:60]}…", flush=True)
        result = answer_question(q["question"])
        rows.append({
            "question": q["question"],
            "type": q["type"],
            "expected": set(q["expected_articles"]),
            "cited": result["cited"],
            "unverified": result["unverified"],
            "abstained": is_abstention(result),
            "score": result["retrieval_score"],
            "error": result["error"],
            "answer": result["answer"],
        })

    elapsed = time.time() - started
    failed = [r for r in rows if r["error"]]
    if failed:
        print(f"\n{len(failed)} appel(s) au modèle en échec — résultats incomplets.")
        return

    in_scope = [r for r in rows if r["type"] == "retrieval"]
    out_scope = [r for r in rows if r["type"] == "abstention"]

    # Critère 2 : citation systématique (sur les réponses non-abstention)
    answered = [r for r in in_scope if not r["abstained"]]
    with_citation = [r for r in answered if r["cited"]]
    citation_rate = len(with_citation) / len(answered) if answered else 0.0

    # Critère 3 : abstention correcte sur les questions hors périmètre
    correct_abstentions = [r for r in out_scope if r["abstained"]]
    abstention_rate = len(correct_abstentions) / len(out_scope) if out_scope else 0.0

    # Abstention à tort : question dans le périmètre mais le système refuse
    wrong_abstentions = [r for r in in_scope if r["abstained"]]

    # Critère 5 : vérification des citations
    total_cited = sum(len(r["cited"]) for r in rows)
    total_unverified = sum(len(r["unverified"]) for r in rows)
    verified_rate = (total_cited - total_unverified) / total_cited if total_cited else 0.0

    # Bonus : l'article attendu est-il réellement cité dans la réponse ?
    correct_source = [r for r in answered if r["expected"] & r["cited"]]
    source_accuracy = len(correct_source) / len(answered) if answered else 0.0

    lines = []
    lines.append("# Résultats d'évaluation — réponses générées\n")
    lines.append(f"Jeu de référence : **{len(in_scope)}** questions dans le périmètre, "
                 f"**{len(out_scope)}** hors périmètre. Durée totale : {elapsed/60:.1f} min.\n")
    lines.append("Ce rapport couvre les critères de succès qui dépendent de la réponse générée. "
                 "Les métriques de recherche pure (Recall@k, MRR — critère 4) sont produites "
                 "séparément par `run_eval.py`.\n")

    lines.append("## Synthèse\n")
    lines.append("| Critère | Mesure | Résultat |")
    lines.append("|---|---|---|")
    lines.append(f"| 2 — Citation systématique | réponses citant ≥ 1 article | "
                 f"**{citation_rate:.0%}** ({len(with_citation)}/{len(answered)}) |")
    lines.append(f"| 3 — Abstention correcte | questions hors périmètre refusées | "
                 f"**{abstention_rate:.0%}** ({len(correct_abstentions)}/{len(out_scope)}) |")
    lines.append(f"| 5 — Vérification des citations | articles cités présents dans le contexte | "
                 f"**{verified_rate:.0%}** ({total_cited - total_unverified}/{total_cited}) |")
    lines.append(f"| — *(bonus)* Justesse de la source | l'article attendu est cité | "
                 f"**{source_accuracy:.0%}** ({len(correct_source)}/{len(answered)}) |")
    lines.append(f"| — Abstentions à tort | questions valides refusées | "
                 f"**{len(wrong_abstentions)}/{len(in_scope)}** |\n")

    if wrong_abstentions:
        lines.append("## Abstentions à tort (questions dans le périmètre refusées)\n")
        for r in wrong_abstentions:
            lines.append(f"- {r['question']} *(attendu : article {', '.join(sorted(r['expected']))} "
                         f"· score de recherche {r['score']:.3f})*")
        lines.append("")

    missed = [r for r in answered if not (r["expected"] & r["cited"])]
    if missed:
        lines.append("## Réponses ne citant pas l'article attendu\n")
        lines.append("Le système a répondu, mais sans citer l'article de référence. "
                     "À examiner : article de référence trop strict, ou réponse fondée "
                     "sur un article voisin (souvent défendable en droit).\n")
        for r in missed:
            lines.append(f"- **{r['question']}**  \n"
                         f"  attendu : {', '.join(sorted(r['expected'])) or '—'} · "
                         f"cité : {', '.join(sorted(r['cited'], key=lambda x: int(x))) or 'aucun'}")
        lines.append("")

    unverified_rows = [r for r in rows if r["unverified"]]
    if unverified_rows:
        lines.append("## Citations non vérifiées\n")
        lines.append("Numéros d'article cités par le modèle mais absents du contexte fourni. "
                     "Inclut les **renvois internes** (« …prévu par l'article N ci-dessous » "
                     "cité depuis le texte d'un article fourni), qui ne sont pas des "
                     "hallucinations — limite connue et documentée de la vérification.\n")
        for r in unverified_rows:
            lines.append(f"- **{r['question']}** → {', '.join(sorted(r['unverified'], key=lambda x: int(x)))}")
        lines.append("")

    lines.append("## Détail par question\n")
    lines.append("| Question | Type | Attendu | Cité | Abstention |")
    lines.append("|---|---|---|---|---|")
    for r in rows:
        cited = ", ".join(sorted(r["cited"], key=lambda x: int(x))) or "—"
        expected = ", ".join(sorted(r["expected"])) or "—"
        q = r["question"].replace("|", "\\|")
        lines.append(f"| {q} | {r['type']} | {expected} | {cited} | "
                     f"{'oui' if r['abstained'] else 'non'} |")

    report = "\n".join(lines) + "\n"
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print("\n" + "=" * 60)
    print(f"Critère 2 — Citation systématique     : {citation_rate:.0%} ({len(with_citation)}/{len(answered)})")
    print(f"Critère 3 — Abstention correcte       : {abstention_rate:.0%} ({len(correct_abstentions)}/{len(out_scope)})")
    print(f"Critère 5 — Vérification des citations: {verified_rate:.0%} ({total_cited - total_unverified}/{total_cited})")
    print(f"Bonus     — Justesse de la source     : {source_accuracy:.0%} ({len(correct_source)}/{len(answered)})")
    print(f"            Abstentions à tort        : {len(wrong_abstentions)}/{len(in_scope)}")
    print("=" * 60)
    print(f"Rapport écrit dans {REPORT_PATH}")


if __name__ == "__main__":
    main()
