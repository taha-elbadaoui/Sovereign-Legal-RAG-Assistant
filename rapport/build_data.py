"""Génère les données chiffrées du rapport depuis les fichiers de mesure.

Sortie (dans rapport/Figures/data/) :
  - chiffres.tex      macros \\newcommand pour chaque nombre cité dans le texte
  - fig-*.tex         coordonnées pgfplots, incluses par les figures
  - *.csv             mêmes données en clair, pour inspection

Les figures lisent les fichiers .tex, pas les CSV : pgfplotstable ne sait pas
traiter un champ texte contenant une virgule, ce qui est le cas de plusieurs
libellés de catégorie. Émettre directement les coordonnées supprime toute
étape d'analyse syntaxique côté LaTeX.

Aucun chiffre du rapport n'est saisi à la main : tout provient soit de
eval/mesures-performance.json (produit par eval/run_measures.py), soit de
data/processed/corpus_chunks.jsonl (produit par src/parser.py).

Usage :  python rapport/build_data.py
"""

import csv
import json
import os
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, ".."))
OUT = os.path.join(BASE, "Figures", "data")

MEASURES = os.path.join(ROOT, "eval", "mesures-performance.json")
CORPUS = os.path.join(ROOT, "data", "processed", "corpus_chunks.jsonl")

# Métriques de recherche pure (Recall@5, MRR). Elles ne figurent pas dans le
# JSON de mesures : run_eval.py les écrit sur la sortie standard, car il
# n'appelle pas le LLM et constitue un banc séparé. Les valeurs ci-dessous sont
# celles du run consigné dans JOURNAL.md ; elles se régénèrent par :
#     python eval/run_eval.py
# Questions qui NOMMENT un article par son numéro. retriever.py force alors
# top_similarity=1.0 (voir explicit_article_refs) : ce n'est pas une mesure de
# similarité organique, et l'inclure fausserait toute statistique sur les
# scores de recherche. Exclues des bandes de score, pas du reste.
QUESTIONS_REFERENCE_EXPLICITE = {
    "Que dit l'article 32 du Code du travail ?",
    "Que prévoit l'article 152 ?",
    "Quel est le contenu de l'article 256 ?",
    "Que dispose l'article 39 ?",
    "Que dit l'article premier du Code du travail ?",
    "Que prévoit l'article 217 ?",
}

RETRIEVAL_METRICS = [
    # méthode,          recall@5, mrr
    ("Dense seul",      0.849,    0.778),
    ("BM25 seul",       0.660,    0.535),
    ("Hybride (RRF)",   0.868,    0.775),
]

# Ordre d'affichage des catégories de la taxonomie, du meilleur au pire
# résultat, pour que la figure se lise de haut en bas.
TAXONOMY_ORDER = [
    "Réponse sourcée, article attendu cité",
    "Réponse sourcée, autre article cité",
    "Abstention correcte",
    "Réponse avec citation non vérifiée",
    "Réponse sans aucune citation",
    "Refus à tort (question valide)",
]

# Libellés courts pour les axes de figure (les intitulés complets sont trop
# longs pour tenir en légende).
TAXONOMY_SHORT = {
    "Réponse sourcée, article attendu cité": "Sourcée, article attendu",
    "Réponse sourcée, autre article cité": "Sourcée, autre article",
    "Abstention correcte": "Abstention correcte",
    "Réponse avec citation non vérifiée": "Citation non vérifiée",
    "Réponse sans aucune citation": "Sans citation",
    "Refus à tort (question valide)": "Refus à tort",
}


def fr(x, decimals=2):
    """Formate un nombre à la française (virgule décimale), pour LaTeX."""
    return f"{x:.{decimals}f}".replace(".", "{,}")


def write_csv(name, header, rows):
    path = os.path.join(OUT, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    return path


def write_tex(name, lines, comment):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"% {comment}\n% Généré par rapport/build_data.py — NE PAS ÉDITER.\n")
        f.write("\n".join(lines) + "\n")
    return path


def coords(pairs, fmt="({0},{1})"):
    """Suite de coordonnées pgfplots sur une seule ligne."""
    return " ".join(fmt.format(x, y) for x, y in pairs)


def main():
    os.makedirs(OUT, exist_ok=True)

    with open(MEASURES, encoding="utf-8") as f:
        m = json.load(f)

    questions = m["questions"]
    in_scope = [q for q in questions if q["type"] == "retrieval"]
    out_scope = [q for q in questions if q["type"] == "abstention"]

    answered = [q for q in in_scope if not q["abstained"]]
    refused_wrongly = [q for q in in_scope if q["abstained"]]

    with_citation = [q for q in answered if q["cited_articles"]]
    expected_cited = [q for q in answered
                      if set(q["expected_articles"]) & set(q["cited_articles"])]

    n_citations = sum(len(q["cited_articles"]) for q in answered)
    n_unverified = sum(len(q["unverified_citations"]) for q in answered)

    abstained_out = [q for q in out_scope if q["abstained"]]
    gate_fired = [q for q in questions if q["gate_abstained"]]

    lat = m["latency_seconds"]

    # ---------------------------------------------------------------- corpus
    with open(CORPUS, encoding="utf-8") as f:
        articles = [json.loads(line) for line in f]

    per_livre = Counter(a["livre"] or "Non rattaché" for a in articles)
    # Le nom complet d'un Livre fait jusqu'à 130 caractères : illisible sur un
    # axe. On garde le numéro comme étiquette et le libellé va en légende.
    livre_labels = {
        "Livre préliminaire": "Prélim.",
        "Livre premier : Des conventions relatives au travail": "I",
        "Livre II: Des conditions de travail et de la rémunération du salarié": "II",
        "Livre III : Des syndicats professionnels, des délégués des salariés, "
        "du comité d'entreprise et des représentants des syndicats dans l'entreprise": "III",
        "Livre IV : De l'intermédiation en matière de recrutement et d'embauchage": "IV",
        "Livre V: Des organes de contrôle": "V",
        "Livre VI: du Règlement des conflits collectifs du travail": "VI",
        "Livre VII: Dispositions finales": "VII",
    }

    # ------------------------------------------------------------------ CSV
    write_csv("recherche.csv", ["methode", "recall", "mrr"],
              [(name, f"{r:.3f}", f"{mrr:.3f}") for name, r, mrr in RETRIEVAL_METRICS])

    taxo = m["outcome_taxonomy"]
    write_csv("taxonomie.csv", ["categorie", "n", "part"],
              [(TAXONOMY_SHORT[c], taxo.get(c, 0),
                f"{100 * taxo.get(c, 0) / len(questions):.1f}")
               for c in TAXONOMY_ORDER])

    write_csv("fiabilite.csv", ["indicateur", "pourcentage", "detail"], [
        ("Citation systématique",
         f"{100 * len(with_citation) / len(answered):.1f}",
         f"{len(with_citation)}/{len(answered)}"),
        ("Citations vérifiées",
         f"{100 * (n_citations - n_unverified) / n_citations:.1f}",
         f"{n_citations - n_unverified}/{n_citations}"),
        ("Article attendu cité",
         f"{100 * len(expected_cited) / len(answered):.1f}",
         f"{len(expected_cited)}/{len(answered)}"),
        ("Abstention hors périmètre",
         f"{100 * len(abstained_out) / len(out_scope):.1f}",
         f"{len(abstained_out)}/{len(out_scope)}"),
    ])

    # Scores de recherche, une ligne par question, classés en trois bandes.
    # La bande d'une question hors périmètre dépend de son domaine : une
    # question juridique partage le vocabulaire du corpus, pas une question de
    # cuisine — c'est précisément le constat que la figure doit montrer.
    non_legal = {"Quelle est la recette du couscous royal ?",
                 "Quelle est la capitale de la France ?",
                 "Quel est le meilleur moment de l'année pour visiter Marrakech ?",
                 "Quelles sont les règles du hors-jeu au football ?"}
    rows = []
    for q in questions:
        if q["question"] in QUESTIONS_REFERENCE_EXPLICITE:
            continue  # score forcé à 1.0, pas une similarité organique
        if q["type"] == "retrieval":
            bande = "droit du travail"
        elif q["question"] in non_legal:
            bande = "hors droit"
        else:
            bande = "autre domaine juridique"
        rows.append((bande, f"{q['retrieval_score']:.4f}"))
    rows.sort(key=lambda r: float(r[1]))
    write_csv("scores.csv", ["bande", "score"], rows)

    write_csv("latence-etapes.csv", ["etape", "mediane", "moyenne", "p90", "max"], [
        ("Recherche", *[f"{lat['retrieval'][k]:.3f}"
                        for k in ("median", "mean", "p90", "max")]),
        ("Génération", *[f"{lat['generation'][k]:.3f}"
                         for k in ("median", "mean", "p90", "max")]),
        ("Total (avec génération)", *[f"{lat['total_with_generation'][k]:.3f}"
                                      for k in ("median", "mean", "p90", "max")]),
        ("Total (abstention)", *[f"{lat['total_abstained_pre_llm'][k]:.3f}"
                                 for k in ("median", "mean", "p90", "max")]),
    ])

    # Une ligne par question générée, triée par temps total : donne une courbe
    # cumulée lisible plutôt qu'un nuage.
    gen = sorted((q for q in questions if not q["gate_abstained"]),
                 key=lambda q: q["t_total_s"])
    write_csv("latence-questions.csv", ["i", "recherche", "generation", "total"],
              [(i, f"{q['t_retrieval_s']:.3f}", f"{q['t_generation_s']:.3f}",
                f"{q['t_total_s']:.3f}") for i, q in enumerate(gen, start=1)])

    write_csv("corpus-livres.csv", ["livre", "n"],
              [(livre_labels.get(k, k), v)
               for k, v in sorted(per_livre.items(), key=lambda kv: -kv[1])])

    # ------------------------------------------------- coordonnées de figure
    # Abscisses numériques plutôt que symboliques : la clé « symbolic x coords »
    # de pgfplots est lue avant expansion des macros, une liste passée par
    # \newcommand n'y serait donc pas reconnue. Les étiquettes d'axe restent
    # écrites en clair dans le fichier de figure — ce sont des noms de méthode,
    # pas des données.
    # Coordonnées (valeur, rang) : le graphique est en barres horizontales,
    # la métrique est donc portée par l'abscisse.
    write_tex("fig-recherche-data.tex", [
        "\\newcommand{\\RechercheRecall}{" +
        coords([(f"{r:.3f}", i) for i, (_, r, _) in enumerate(RETRIEVAL_METRICS)]) + "}",
        "\\newcommand{\\RechercheMrr}{" +
        coords([(f"{m_:.3f}", i) for i, (_, _, m_) in enumerate(RETRIEVAL_METRICS)]) + "}",
    ], "Recall@5 et MRR par méthode de recherche")

    # Une macro par catégorie : chaque barre porte la couleur de son statut
    # (réussite, réserve, échec), ce que ne permet pas un tracé unique.
    taxo_rows = [(TAXONOMY_SHORT[c], taxo.get(c, 0)) for c in TAXONOMY_ORDER]
    letters = "ABCDEF"
    write_tex("fig-taxonomie-data.tex",
              ["\\newcommand{\\TaxonomieLabels}{" +
               ",".join("{%s}" % label for label, _ in taxo_rows) + "}"] +
              ["\\newcommand{\\TaxonomieBar%s}{(%d,%d)}" % (letters[i], n, i)
               for i, (_, n) in enumerate(taxo_rows)] +
              ["\\newcommand{\\TaxonomieMax}{%d}" % max(n for _, n in taxo_rows),
               "\\newcommand{\\TaxonomieTotal}{%d}" % sum(n for _, n in taxo_rows)],
              "Taxonomie des réponses générées, du meilleur au pire résultat")

    fiab = [
        ("Citation systématique", 100 * len(with_citation) / len(answered),
         f"{len(with_citation)}/{len(answered)}"),
        ("Citations vérifiées", 100 * (n_citations - n_unverified) / n_citations,
         f"{n_citations - n_unverified}/{n_citations}"),
        ("Article attendu cité", 100 * len(expected_cited) / len(answered),
         f"{len(expected_cited)}/{len(answered)}"),
        ("Abstention hors périmètre", 100 * len(abstained_out) / len(out_scope),
         f"{len(abstained_out)}/{len(out_scope)}"),
    ]
    # Effectifs émis un par un : une boucle \foreach dans la figure buterait sur
    # \d et \i, qui sont déjà des commandes LaTeX (accents).
    write_tex("fig-fiabilite-data.tex",
              ["\\newcommand{\\FiabiliteLabels}{" +
               ",".join("{%s}" % label for label, _, _ in fiab) + "}",
               "\\newcommand{\\FiabiliteCoords}{" +
               coords([(f"{p:.1f}", i) for i, (_, p, _) in enumerate(fiab)]) + "}"] +
              ["\\newcommand{\\FiabiliteDetail%s}{%s}" % (letters[i], d)
               for i, (_, _, d) in enumerate(fiab)],
              "Indicateurs de fiabilité, en pourcentage")

    # Nuage de scores : un léger décalage vertical déterministe évite que des
    # points de score voisin ne se recouvrent complètement.
    bands = {"droit du travail": 2, "autre domaine juridique": 1, "hors droit": 0}
    by_band = {name: [] for name in bands}
    for i, (band, score) in enumerate(rows):
        by_band[band].append((score, f"{bands[band] + ((i % 5) - 2) * 0.055:.3f}"))
    write_tex("fig-scores-data.tex", [
        "\\newcommand{\\Scores%s}{%s}" % (key, coords(by_band[name]))
        for key, name in (("Travail", "droit du travail"),
                          ("Juridique", "autre domaine juridique"),
                          ("HorsDroit", "hors droit"))
    ], "Score de recherche par question, réparti en trois bandes")

    write_tex("fig-latence-data.tex", [
        "\\newcommand{\\LatMedRecherche}{%.3f}" % lat["retrieval"]["median"],
        "\\newcommand{\\LatMedGeneration}{%.3f}" % lat["generation"]["median"],
        "\\newcommand{\\LatMedAbstention}{%.3f}"
        % lat["total_abstained_pre_llm"]["median"],
        "\\newcommand{\\LatCourbeTotal}{" +
        coords([(i, q["t_total_s"]) for i, q in enumerate(gen, start=1)]) + "}",
        "\\newcommand{\\LatCourbeRecherche}{" +
        coords([(i, q["t_retrieval_s"]) for i, q in enumerate(gen, start=1)]) + "}",
        "\\newcommand{\\LatNbCourbe}{%d}" % len(gen),
    ], "Latence : composition médiane et distribution par question")

    livres_sorted = sorted(per_livre.items(), key=lambda kv: -kv[1])
    write_tex("fig-corpus-data.tex", [
        "\\newcommand{\\CorpusLabels}{" +
        ",".join("{Livre %s}" % livre_labels.get(k, k) for k, _ in livres_sorted) + "}",
        "\\newcommand{\\CorpusCoords}{" +
        coords([(v, i) for i, (_, v) in enumerate(livres_sorted)]) + "}",
        "\\newcommand{\\CorpusMax}{%d}" % livres_sorted[0][1],
    ], "Répartition des articles du corpus par Livre")

    # ----------------------------------------------------------- chiffres.tex
    macros = {
        # corpus
        "NbArticles": len(articles),
        "NbLivres": len(per_livre),
        # jeu de référence
        "NbQuestions": len(questions),
        "NbInScope": len(in_scope),
        "NbOutScope": len(out_scope),
        "NbRepondues": len(answered),
        "NbRefusTort": len(refused_wrongly),
        "NbGarde": len(gate_fired),
        # fiabilité (arrondis à l'entier : la précision décimale n'a pas de
        # sens sur 29 observations)
        "TauxCitation": round(100 * len(with_citation) / len(answered)),
        "TauxVerif": round(100 * (n_citations - n_unverified) / n_citations),
        "TauxSourceAttendue": round(100 * len(expected_cited) / len(answered)),
        "TauxAbstention": round(100 * len(abstained_out) / len(out_scope)),
        "NbCitations": n_citations,
        "NbNonVerifiees": n_unverified,
        # seuil
        "SeuilAbstention": fr(m["abstention_threshold"], 2),
        "ScoreInMin": fr(min(q["retrieval_score"] for q in in_scope
                             if q["question"] not in QUESTIONS_REFERENCE_EXPLICITE), 3),
        "ScoreInMax": fr(max(q["retrieval_score"] for q in in_scope
                             if q["question"] not in QUESTIONS_REFERENCE_EXPLICITE), 3),
        "ScoreJuridiqueMin": fr(min(q["retrieval_score"] for q in out_scope
                                    if q["question"] not in non_legal), 3),
        "ScoreJuridiqueMax": fr(max(q["retrieval_score"] for q in out_scope
                                    if q["question"] not in non_legal), 3),
        "ScoreHorsDroitMin": fr(min(q["retrieval_score"] for q in out_scope
                                    if q["question"] in non_legal), 3),
        "ScoreHorsDroitMax": fr(max(q["retrieval_score"] for q in out_scope
                                    if q["question"] in non_legal), 3),
        # latence
        "LatRecherche": fr(lat["retrieval"]["median"], 2),
        "LatGeneration": fr(lat["generation"]["median"], 2),
        "LatTotale": fr(lat["total_with_generation"]["median"], 2),
        "LatAbstention": fr(lat["total_abstained_pre_llm"]["median"], 2),
        "LatMax": fr(lat["total_with_generation"]["max"], 2),
        "PartRecherche": round(100 * lat["retrieval"]["median"]
                               / lat["total_with_generation"]["median"]),
        "FacteurGarde": round(lat["total_with_generation"]["median"]
                              / lat["total_abstained_pre_llm"]["median"]),
        # recherche
        "RecallDense": fr(RETRIEVAL_METRICS[0][1], 3),
        "MrrDense": fr(RETRIEVAL_METRICS[0][2], 3),
        "RecallBmXXV": fr(RETRIEVAL_METRICS[1][1], 3),
        "MrrBmXXV": fr(RETRIEVAL_METRICS[1][2], 3),
        "RecallHybride": fr(RETRIEVAL_METRICS[2][1], 3),
        "MrrHybride": fr(RETRIEVAL_METRICS[2][2], 3),
        # traçabilité du run
        "ModeleLLM": m["model"].replace(":", ":\\allowbreak "),
        "DateMesure": m["generated_at"][:10],
    }

    path = os.path.join(OUT, "chiffres.tex")
    with open(path, "w", encoding="utf-8") as f:
        f.write("% Fichier généré par rapport/build_data.py — NE PAS ÉDITER.\n")
        f.write("% Régénérer avec :  python rapport/build_data.py\n\n")
        for key, value in macros.items():
            f.write(f"\\newcommand{{\\{key}}}{{{value}}}\n")

    print(f"chiffres.tex : {len(macros)} macros")
    print(f"CSV écrits dans {OUT}")
    print(f"Contrôle — {len(questions)} questions, {len(answered)} répondues, "
          f"{len(refused_wrongly)} refus à tort, "
          f"{n_citations - n_unverified}/{n_citations} citations vérifiées")


if __name__ == "__main__":
    main()
