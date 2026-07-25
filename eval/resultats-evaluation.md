# Résultats d'évaluation — réponses générées

Jeu de référence : **32** questions dans le périmètre, **5** hors périmètre. Durée totale : 2.3 min.

Ce rapport couvre les critères de succès qui dépendent de la réponse générée. Les métriques de recherche pure (Recall@k, MRR — critère 4) sont produites séparément par `run_eval.py`.

## Synthèse

| Critère | Mesure | Résultat |
|---|---|---|
| 2 — Citation systématique | réponses citant ≥ 1 article | **97%** (30/31) |
| 3 — Abstention correcte | questions hors périmètre refusées | **100%** (5/5) |
| 5 — Vérification des citations | articles cités présents dans le contexte | **91%** (49/54) |
| — *(bonus)* Justesse de la source | l'article attendu est cité | **84%** (26/31) |
| — Abstentions à tort | questions valides refusées | **1/32** |

## Abstentions à tort (questions dans le périmètre refusées)

- Peut-on employer un mineur de moins de 18 ans dans les mines ? *(attendu : article 179 · score de recherche 0.718)*

## Réponses ne citant pas l'article attendu

Le système a répondu, mais sans citer l'article de référence. À examiner : article de référence trop strict, ou réponse fondée sur un article voisin (souvent défendable en droit).

- **Quelles catégories de salariés sont régies par des statuts spéciaux ?**  
  attendu : 3 · cité : 4, 11
- **Quelle est la durée minimale du repos hebdomadaire ?**  
  attendu : 205 · cité : 206, 215
- **À partir de combien de salariés doit-on élire des délégués des salariés ?**  
  attendu : 430 · cité : 433
- **Quelle est la durée maximale d'une mission d'intérim ?**  
  attendu : 500 · cité : aucun
- **À partir de combien de salariés un comité de sécurité et d'hygiène est-il obligatoire ?**  
  attendu : 336 · cité : 337

## Citations non vérifiées

Numéros d'article cités par le modèle mais absents du contexte fourni. Inclut les **renvois internes** (« …prévu par l'article N ci-dessous » cité depuis le texte d'un article fourni), qui ne sont pas des hallucinations — limite connue et documentée de la vérification.

- **Dans quel délai faut-il saisir le tribunal après un licenciement contesté ?** → 532
- **À quel âge un salarié est-il mis à la retraite ?** → 53
- **Comment sont calculés les dommages-intérêts en cas de licenciement abusif ?** → 532
- **Comment est calculée l'indemnité de licenciement ?** → 41, 51

## Détail par question

| Question | Type | Attendu | Cité | Abstention |
|---|---|---|---|---|
| Quelle est la durée de la période d'essai pour un cadre en contrat à durée indéterminée ? | retrieval | 14 | 14 | non |
| À quel âge minimum un mineur peut-il être employé au Maroc ? | retrieval | 143 | 143, 145 | non |
| Quelle est la durée du congé de maternité ? | retrieval | 152 | 152, 154, 156 | non |
| Quelle est la durée légale du travail dans les activités non agricoles ? | retrieval | 184 | 184 | non |
| Dans quel délai faut-il saisir le tribunal après un licenciement contesté ? | retrieval | 65 | 41, 65, 532 | non |
| À quel âge un salarié est-il mis à la retraite ? | retrieval | 526 | 53, 526 | non |
| Le harcèlement sexuel commis par l'employeur est-il une faute grave ? | retrieval | 40 | 39, 40 | non |
| Peut-on employer un mineur de moins de 18 ans dans les mines ? | retrieval | 179 | 179, 180 | oui |
| Combien d'heures par mois un délégué des salariés a-t-il pour exercer ses fonctions ? | retrieval | 456 | 456 | non |
| Quelles catégories de salariés sont régies par des statuts spéciaux ? | retrieval | 3 | 4, 11 | non |
| Pour combien de temps peut-on conclure un CDD à l'ouverture d'une nouvelle entreprise ? | retrieval | 17 | 17 | non |
| Combien de jours de congé annuel payé acquiert-on par mois de service ? | retrieval | 231 | 231, 235, 238 | non |
| Quelle est la durée minimale du repos hebdomadaire ? | retrieval | 205 | 206, 215 | non |
| Combien de jours de congé un salarié a-t-il à l'occasion d'une naissance ? | retrieval | 269 | 269 | non |
| À partir de quelle ancienneté la prime d'ancienneté est-elle due, et à quel taux ? | retrieval | 350 | 350 | non |
| Quelles sont les fautes graves pouvant justifier le licenciement d'un salarié ? | retrieval | 39 | 39, 40, 293 | non |
| Comment sont calculés les dommages-intérêts en cas de licenciement abusif ? | retrieval | 41 | 41, 532 | non |
| Comment est calculée l'indemnité de licenciement ? | retrieval | 53 | 41, 51, 53, 55, 56 | non |
| L'employeur peut-il licencier une salariée enceinte ? | retrieval | 159 | 159, 160 | non |
| Une mère salariée a-t-elle droit à un repos pour allaiter son enfant ? | retrieval | 161 | 161 | non |
| Est-il permis de faire travailler les salariés pendant les jours de fête payés ? | retrieval | 217 | 217 | non |
| La discrimination salariale entre hommes et femmes est-elle autorisée ? | retrieval | 346 | 346 | non |
| À partir de combien de salariés doit-on élire des délégués des salariés ? | retrieval | 430 | 433 | non |
| À partir de combien de salariés faut-il créer un comité d'entreprise ? | retrieval | 464 | 464 | non |
| Faut-il une autorisation pour recruter un salarié étranger ? | retrieval | 516 | 516 | non |
| Le salarié doit-il être entendu avant d'être licencié ? | retrieval | 62 | 62 | non |
| Quelle est la durée maximale d'une mission d'intérim ? | retrieval | 500 | — | non |
| À partir de combien de salariés un comité de sécurité et d'hygiène est-il obligatoire ? | retrieval | 336 | 337 | non |
| Que doit faire un salarié malade pour justifier son absence ? | retrieval | 271 | 271 | non |
| Combien de jours d'absence a-t-on pour son propre mariage ? | retrieval | 274 | 274 | non |
| Quelles obligations de sécurité et de santé l'employeur a-t-il envers ses salariés ? | retrieval | 24, 281 | 24, 287, 504, 542 | non |
| Un salarié appelé au service militaire retrouve-t-il son poste au retour ? | retrieval | 510 | 510 | non |
| Quelle est la procédure pour divorcer au Maroc ? | abstention | — | — | oui |
| Comment créer une société anonyme au Maroc ? | abstention | — | — | oui |
| Quelle est la peine encourue pour vol qualifié ? | abstention | — | — | oui |
| Quelle est la recette du couscous royal ? | abstention | — | — | oui |
| Quelle est la capitale de la France ? | abstention | — | — | oui |
