"""Full statistical measurement of the assistant — latency + outcome taxonomy.

Complements the other two evaluation scripts:
  run_eval.py         -> retrieval only (Recall@k, MRR), no LLM, fast
  run_answer_eval.py  -> pass/fail against the plan's success criteria (§7)
  run_measures.py     -> this one: timing statistics, an outcome taxonomy, and
                         SVG figures for the report

Run from the repo root (needs Ollama):  python eval/run_measures.py

WHAT THIS CAN AND CANNOT MEASURE
--------------------------------
Measured directly:
  - latency, split into retrieval vs generation
  - whether an answer cites anything at all
  - whether every cited article was actually in the supplied context
  - whether the expected (gold) article is among those cited
  - whether out-of-scope questions are refused

NOT measured (stated plainly rather than papered over):
  Semantic faithfulness. Checking that a cited article *was supplied* is not the
  same as checking that it *says what the answer claims*. An answer citing a real,
  supplied article while mis-describing its content is counted here as grounded.
  Detecting that needs entailment checking or human review; the
  "citation non vérifiée" count below is a proxy signal, not a hallucination count.
"""
import os
import sys
import json
import csv
import statistics as stats

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import answer_question, ABSTENTION_THRESHOLD  # noqa: E402
from generator import MODEL                            # noqa: E402
import svg_charts as C                                 # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
REF_PATH = os.path.join(HERE, "reference_qa.jsonl")
FIG_DIR = os.path.join(HERE, "figures")
REPORT = os.path.join(HERE, "mesures-performance.md")
JSON_EXPORT = os.path.join(HERE, "mesures-performance.json")
CSV_EXPORT = os.path.join(HERE, "mesures-performance.csv")

ABSTENTION_MARKERS = ["ne dispose pas d'information suffisante"]

# Outcome taxonomy ---------------------------------------------------------- #
GROUNDED_EXPECTED = "Réponse sourcée, article attendu cité"
GROUNDED_OTHER = "Réponse sourcée, autre article cité"
UNVERIFIED = "Réponse avec citation non vérifiée"
NO_CITATION = "Réponse sans aucune citation"
FALSE_REFUSAL = "Refus à tort (question valide)"
CORRECT_ABSTENTION = "Abstention correcte"
MISSED_ABSTENTION = "Répond alors qu'il devrait s'abstenir"

TAXONOMY_COLOURS = {
    GROUNDED_EXPECTED: C.GREEN,
    GROUNDED_OTHER: "#65a30d",
    UNVERIFIED: C.AMBER,
    NO_CITATION: "#f59e0b",
    FALSE_REFUSAL: C.RED,
    CORRECT_ABSTENTION: C.GREEN,
    MISSED_ABSTENTION: C.RED,
}


def is_abstention(result):
    if result["abstained"]:
        return True
    text = (result["answer"] or "").lower()
    return any(m in text for m in ABSTENTION_MARKERS)


def classify(row):
    if row["type"] == "abstention":
        return CORRECT_ABSTENTION if row["abstained"] else MISSED_ABSTENTION
    if row["abstained"]:
        return FALSE_REFUSAL
    if not row["cited"]:
        return NO_CITATION
    if row["unverified"]:
        return UNVERIFIED
    if row["expected"] & row["cited"]:
        return GROUNDED_EXPECTED
    return GROUNDED_OTHER


def pct(n, d):
    return f"{100*n/d:.0f} %" if d else "—"


def describe(values):
    if not values:
        return {}
    ordered = sorted(values)
    return {
        "n": len(values),
        "min": min(values),
        "median": stats.median(values),
        "mean": stats.fmean(values),
        "p90": ordered[max(0, min(len(ordered) - 1, int(round(0.9 * (len(ordered) - 1)))))],
        "max": max(values),
    }


def main():
    with open(REF_PATH, encoding="utf-8") as f:
        reference = [json.loads(l) for l in f]

    os.makedirs(FIG_DIR, exist_ok=True)
    rows = []

    for i, q in enumerate(reference, 1):
        print(f"[{i}/{len(reference)}] {q['question'][:58]}…", flush=True)
        r = answer_question(q["question"])
        if r["error"]:
            print(f"\n  Modèle injoignable : {r['error']}")
            return
        rows.append({
            "question": q["question"],
            "type": q["type"],
            "expected": set(q["expected_articles"]),
            "cited": r["cited"],
            "unverified": r["unverified"],
            "abstained": is_abstention(r),
            "gate_abstained": r["abstained"],
            "score": r["retrieval_score"],
            "t_retrieval": r["timings"]["retrieval"],
            "t_generation": r["timings"]["generation"],
            "t_total": r["timings"]["total"],
            "answer": r["answer"],
        })

    for row in rows:
        row["outcome"] = classify(row)

    in_scope = [r for r in rows if r["type"] == "retrieval"]
    out_scope = [r for r in rows if r["type"] == "abstention"]
    generated = [r for r in rows if not r["gate_abstained"]]
    gated = [r for r in rows if r["gate_abstained"]]

    t_all = describe([r["t_total"] for r in rows])
    t_gen = describe([r["t_total"] for r in generated])
    t_gate = describe([r["t_total"] for r in gated])
    t_ret = describe([r["t_retrieval"] for r in rows])
    t_llm = describe([r["t_generation"] for r in generated])

    # ---------------------------------------------------------------- figures
    figs = []

    C_write = lambda name, svg: (  # noqa: E731
        open(os.path.join(FIG_DIR, name), "w", encoding="utf-8").write(svg), figs.append(name))

    C_write("latence-repartition.svg", C.hbar(
        "Latence — répartition du temps de réponse (secondes)",
        [("Recherche (médiane)", round(t_ret["median"], 2), C.BLUE),
         ("Génération LLM (médiane)", round(t_llm["median"], 2), C.AMBER),
         ("Total avec génération (médiane)", round(t_gen["median"], 2), C.INK),
         ("Total, abstention pré-LLM (médiane)", round(t_gate["median"], 2), C.GREEN)],
        unit=" s",
        note="L'abstention pré-LLM ne paie que la recherche : le modèle n'est jamais appelé."))

    C_write("latence-distribution.svg", C.histogram(
        "Distribution du temps de réponse total",
        [r["t_total"] for r in rows], bins=10,
        xlabel="secondes", colour=C.BLUE,
        note=f"n = {len(rows)} questions · modèle {MODEL} en local"))

    counts = {}
    for r in rows:
        counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
    order = [GROUNDED_EXPECTED, GROUNDED_OTHER, UNVERIFIED, NO_CITATION,
             FALSE_REFUSAL, CORRECT_ABSTENTION, MISSED_ABSTENTION]
    segs = [(k, counts[k], TAXONOMY_COLOURS[k]) for k in order if counts.get(k)]
    C_write("taxonomie-resultats.svg", C.stacked(
        f"Classement des {len(rows)} réponses",
        segs,
        note="« citation non vérifiée » = article cité absent du contexte fourni "
             "(souvent un renvoi interne), pas une hallucination prouvée."))

    C_write("separation-abstention.svg", C.strip(
        "Score de recherche : questions dans le périmètre vs hors périmètre",
        [("Dans le périmètre", [r["score"] for r in in_scope if not r["gate_abstained"]], C.GREEN),
         ("Hors périmètre", [r["score"] for r in out_scope], C.RED)],
        threshold=ABSTENTION_THRESHOLD,
        xlabel="similarité cosinus maximale (dense)",
        note="Chaque point est une question. Le seuil ne filtre que la bande clairement non pertinente."))

    ok = counts.get(GROUNDED_EXPECTED, 0) + counts.get(GROUNDED_OTHER, 0)
    C_write("fiabilite-synthese.svg", C.grouped_bars(
        "Fiabilité — indicateurs clés (%)",
        ["Citation\nsystématique", "Abstention\ncorrecte", "Citations\nvérifiées", "Article\nattendu cité"],
        [("mesuré", [
            round(100 * len([r for r in in_scope if r["cited"]]) / max(1, len([r for r in in_scope if not r["abstained"]]))),
            round(100 * len([r for r in out_scope if r["abstained"]]) / max(1, len(out_scope))),
            round(100 * (sum(len(r["cited"]) for r in rows) - sum(len(r["unverified"]) for r in rows))
                  / max(1, sum(len(r["cited"]) for r in rows))),
            round(100 * len([r for r in in_scope if r["expected"] & r["cited"]]) / max(1, len([r for r in in_scope if not r["abstained"]]))),
        ], C.BLUE)],
        unit=" %",
        note=f"n = {len(in_scope)} questions dans le périmètre, {len(out_scope)} hors périmètre"))

    # ----------------------------------------------------------------- report
    L = []
    L.append("# Mesures de performance — Assistant juridique RAG\n")
    L.append(f"Jeu de référence : **{len(in_scope)}** questions dans le périmètre, "
             f"**{len(out_scope)}** hors périmètre. Modèle local : `{MODEL}`.\n")
    L.append("> Toutes les valeurs de ce document sont produites par "
             "`python eval/run_measures.py` — aucune n'est saisie à la main.\n")

    L.append("## 1. Latence\n")
    L.append("| Étape | Médiane | Moyenne | p90 | Max |")
    L.append("|---|---|---|---|---|")
    L.append(f"| Recherche (toutes questions) | {t_ret['median']:.2f} s | {t_ret['mean']:.2f} s | {t_ret['p90']:.2f} s | {t_ret['max']:.2f} s |")
    L.append(f"| Génération LLM | {t_llm['median']:.2f} s | {t_llm['mean']:.2f} s | {t_llm['p90']:.2f} s | {t_llm['max']:.2f} s |")
    L.append(f"| **Total (avec génération)** | **{t_gen['median']:.2f} s** | {t_gen['mean']:.2f} s | {t_gen['p90']:.2f} s | {t_gen['max']:.2f} s |")
    if t_gate:
        L.append(f"| **Total (abstention pré-LLM)** | **{t_gate['median']:.2f} s** | {t_gate['mean']:.2f} s | {t_gate['p90']:.2f} s | {t_gate['max']:.2f} s |")
    L.append("")
    if t_gate and t_gate.get("median"):
        L.append(f"Le garde-fou d'abstention divise le temps de réponse par "
                 f"**{t_gen['median']/t_gate['median']:.0f}×** sur les questions hors périmètre "
                 f"({t_gate['median']:.2f} s contre {t_gen['median']:.2f} s) : le modèle n'est pas appelé du tout.\n")
    L.append(f"La recherche représente environ **{100*t_ret['median']/t_gen['median']:.0f} %** "
             f"du temps total ; le reste est l'inférence du modèle local.\n")
    L.append("![Répartition de la latence](figures/latence-repartition.svg)\n")
    L.append("![Distribution du temps de réponse](figures/latence-distribution.svg)\n")

    L.append("## 2. Classement des réponses\n")
    L.append("| Catégorie | Nombre | Part |")
    L.append("|---|---|---|")
    for k in order:
        if counts.get(k):
            L.append(f"| {k} | {counts[k]} | {pct(counts[k], len(rows))} |")
    L.append("")
    L.append("![Taxonomie des résultats](figures/taxonomie-resultats.svg)\n")

    L.append("### Ce que ces catégories veulent dire\n")
    L.append("- **Réponse sourcée, article attendu cité** — le système répond et cite l'article "
             "de référence prévu par le jeu de test.")
    L.append("- **Réponse sourcée, autre article cité** — réponse fondée sur un article voisin. "
             "Souvent défendable en droit (p. ex. citer 337 au lieu de 336), à trancher au cas par cas.")
    L.append("- **Citation non vérifiée** — un numéro cité n'était pas dans le contexte fourni. "
             "Dans la pratique il s'agit surtout de **renvois internes** (« …prévu par l'article N "
             "ci-dessous ») repris depuis le texte d'un article bien fourni. Signal de vigilance, "
             "**pas** une hallucination démontrée.")
    L.append("- **Refus à tort** — question légitime refusée : c'est le coût d'une abstention trop stricte.")
    L.append("- **Répond alors qu'il devrait s'abstenir** — le cas le plus grave : le système "
             "produit une réponse sur un sujet absent du corpus.\n")

    L.append("## 3. Garde-fou d'abstention\n")
    L.append("![Séparation des scores](figures/separation-abstention.svg)\n")
    in_sc = [r["score"] for r in in_scope]
    out_sc = [r["score"] for r in out_scope]
    L.append(f"- Questions dans le périmètre : score de **{min(in_sc):.3f}** à **{max(in_sc):.3f}**")
    L.append(f"- Questions hors périmètre : score de **{min(out_sc):.3f}** à **{max(out_sc):.3f}**")
    L.append(f"- Seuil retenu : **{ABSTENTION_THRESHOLD}**\n")
    L.append("Le seuil ne cherche pas à séparer le droit du travail des autres domaines juridiques — "
             "il ne filtre que la bande clairement non pertinente. Les questions juridiques hors corpus "
             "passent le seuil et sont rattrapées par l'abstention au niveau du prompt.\n")

    L.append("## 4. Fiabilité — indicateurs\n")
    L.append("![Indicateurs de fiabilité](figures/fiabilite-synthese.svg)\n")

    L.append("## 5. Limite de mesure assumée\n")
    L.append("La vérification des citations contrôle qu'un article cité **figurait dans le contexte "
             "fourni** — pas qu'il **dise réellement** ce que la réponse lui attribue. Une réponse "
             "citant un article réel en en déformant le contenu est comptée ici comme sourcée. "
             "Détecter ce cas demanderait une vérification d'implication (entailment) ou une relecture "
             "humaine ; c'est hors périmètre du stage et documenté comme tel.\n")

    L.append("## 6. Détail par question\n")
    L.append("| Question | Type | Total (s) | Recherche (s) | Score | Attendu | Cité | Classement |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda x: -x["t_total"]):
        q = r["question"].replace("|", "\\|")
        exp = ", ".join(sorted(r["expected"])) or "—"
        cit = ", ".join(sorted(r["cited"], key=int)) or "—"
        L.append(f"| {q} | {r['type']} | {r['t_total']:.2f} | {r['t_retrieval']:.2f} | "
                 f"{r['score']:.3f} | {exp} | {cit} | {r['outcome']} |")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    # ------------------------------------------------------------- JSON export
    import datetime
    payload = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "model": MODEL,
        "abstention_threshold": ABSTENTION_THRESHOLD,
        "reference_set": {"in_scope": len(in_scope), "out_of_scope": len(out_scope)},
        "latency_seconds": {
            "retrieval": t_ret,
            "generation": t_llm,
            "total_with_generation": t_gen,
            "total_abstained_pre_llm": t_gate,
        },
        "outcome_taxonomy": {k: counts[k] for k in order if counts.get(k)},
        "questions": [
            {
                "question": r["question"],
                "type": r["type"],
                "expected_articles": sorted(r["expected"]),
                "cited_articles": sorted(r["cited"], key=int),
                "unverified_citations": sorted(r["unverified"], key=int),
                "abstained": r["abstained"],
                "gate_abstained": r["gate_abstained"],
                "retrieval_score": round(r["score"], 4),
                "t_retrieval_s": round(r["t_retrieval"], 3),
                "t_generation_s": round(r["t_generation"], 3),
                "t_total_s": round(r["t_total"], 3),
                "outcome": r["outcome"],
                # Le texte de la réponse est conservé : sans lui, une citation
                # signalée « non vérifiée » n'est plus diagnosticable après coup
                # (impossible de distinguer un renvoi interne d'une invention
                # ou d'un faux positif du détecteur de citations).
                "answer": r["answer"],
            }
            for r in rows
        ],
    }
    with open(JSON_EXPORT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # -------------------------------------------------------------- CSV export
    with open(CSV_EXPORT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["question", "type", "expected_articles", "cited_articles",
                    "unverified_citations", "abstained", "gate_abstained",
                    "retrieval_score", "t_retrieval_s", "t_generation_s",
                    "t_total_s", "outcome"])
        for r in rows:
            w.writerow([
                r["question"], r["type"],
                ";".join(sorted(r["expected"])),
                ";".join(sorted(r["cited"], key=int)),
                ";".join(sorted(r["unverified"], key=int)),
                r["abstained"], r["gate_abstained"],
                round(r["score"], 4), round(r["t_retrieval"], 3),
                round(r["t_generation"], 3), round(r["t_total"], 3),
                r["outcome"],
            ])

    print("\n" + "=" * 62)
    print(f"Latence médiane (avec génération) : {t_gen['median']:.2f} s")
    if t_gate:
        print(f"Latence médiane (abstention)      : {t_gate['median']:.2f} s")
    print(f"Recherche médiane                 : {t_ret['median']:.2f} s")
    print("-" * 62)
    for k in order:
        if counts.get(k):
            print(f"{k:.<46}{counts[k]:>3}  ({pct(counts[k], len(rows))})")
    print("=" * 62)
    print(f"Rapport  : {REPORT}")
    print(f"JSON     : {JSON_EXPORT}")
    print(f"CSV      : {CSV_EXPORT}  (ouvre directement dans Excel)")
    print(f"Figures  : {FIG_DIR} ({len(figs)} SVG)")


if __name__ == "__main__":
    main()
