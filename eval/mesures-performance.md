# Mesures de performance — Assistant juridique RAG

Jeu de référence : **53** questions dans le périmètre, **9** hors périmètre. Modèle local : `mistral:7b`.

> Toutes les valeurs de ce document sont produites par `python eval/run_measures.py` — aucune n'est saisie à la main.

## 1. Latence

| Étape | Médiane | Moyenne | p90 | Max |
|---|---|---|---|---|
| Recherche (toutes questions) | 0.16 s | 0.17 s | 0.21 s | 0.35 s |
| Génération LLM | 3.83 s | 4.82 s | 10.05 s | 16.15 s |
| **Total (avec génération)** | **3.98 s** | 4.99 s | 10.26 s | 16.32 s |
| **Total (abstention pré-LLM)** | **0.13 s** | 0.13 s | 0.14 s | 0.14 s |

Le garde-fou d'abstention divise le temps de réponse par **30×** sur les questions hors périmètre (0.13 s contre 3.98 s) : le modèle n'est pas appelé du tout.

La recherche représente environ **4 %** du temps total ; le reste est l'inférence du modèle local.

![Répartition de la latence](figures/latence-repartition.svg)

![Distribution du temps de réponse](figures/latence-distribution.svg)

## 2. Classement des réponses

| Catégorie | Nombre | Part |
|---|---|---|
| Réponse sourcée, article attendu cité | 41 | 66 % |
| Réponse sourcée, autre article cité | 2 | 3 % |
| Réponse avec citation non vérifiée | 6 | 10 % |
| Réponse sans aucune citation | 2 | 3 % |
| Refus à tort (question valide) | 2 | 3 % |
| Abstention correcte | 9 | 15 % |

![Taxonomie des résultats](figures/taxonomie-resultats.svg)

### Ce que ces catégories veulent dire

- **Réponse sourcée, article attendu cité** — le système répond et cite l'article de référence prévu par le jeu de test.
- **Réponse sourcée, autre article cité** — réponse fondée sur un article voisin. Souvent défendable en droit (p. ex. citer 337 au lieu de 336), à trancher au cas par cas.
- **Citation non vérifiée** — un numéro cité n'était pas dans le contexte fourni. Dans la pratique il s'agit surtout de **renvois internes** (« …prévu par l'article N ci-dessous ») repris depuis le texte d'un article bien fourni. Signal de vigilance, **pas** une hallucination démontrée.
- **Refus à tort** — question légitime refusée : c'est le coût d'une abstention trop stricte.
- **Répond alors qu'il devrait s'abstenir** — le cas le plus grave : le système produit une réponse sur un sujet absent du corpus.

## 3. Garde-fou d'abstention

![Séparation des scores](figures/separation-abstention.svg)

- Questions dans le périmètre : score de **0.596** à **1.000**
- Questions hors périmètre : score de **0.307** à **0.603**
- Seuil retenu : **0.42**

Le seuil ne cherche pas à séparer le droit du travail des autres domaines juridiques — il ne filtre que la bande clairement non pertinente. Les questions juridiques hors corpus passent le seuil et sont rattrapées par l'abstention au niveau du prompt.

## 4. Fiabilité — indicateurs

![Indicateurs de fiabilité](figures/fiabilite-synthese.svg)

## 5. Limite de mesure assumée

La vérification des citations contrôle qu'un article cité **figurait dans le contexte fourni** — pas qu'il **dise réellement** ce que la réponse lui attribue. Une réponse citant un article réel en en déformant le contenu est comptée ici comme sourcée. Détecter ce cas demanderait une vérification d'implication (entailment) ou une relecture humaine ; c'est hors périmètre du stage et documenté comme tel.

## 6. Détail par question

| Question | Type | Total (s) | Recherche (s) | Score | Attendu | Cité | Classement |
|---|---|---|---|---|---|---|---|
| Quelles sont les fautes graves pouvant justifier le licenciement d'un salarié ? | retrieval | 16.32 | 0.16 | 0.781 | 39 | 39, 40, 160, 293 | Réponse sourcée, article attendu cité |
| Que dispose l'article 39 ? | retrieval | 14.90 | 0.15 | 1.000 | 39 | 39 | Réponse sourcée, article attendu cité |
| Quelles sont les étapes de la procédure de règlement d'un conflit collectif ? | retrieval | 11.52 | 0.19 | 0.613 | 551, 565 | 550, 551, 560, 567 | Réponse sourcée, article attendu cité |
| Quelles catégories de salariés sont régies par des statuts spéciaux ? | retrieval | 10.90 | 0.15 | 0.695 | 3 | 3, 4 | Refus à tort (question valide) |
| Quand le Code du travail entre-t-il en vigueur ? | retrieval | 10.78 | 0.21 | 0.605 | 589 | 58, 100 | Réponse avec citation non vérifiée |
| À partir de combien de salariés doit-on élire des délégués des salariés ? | retrieval | 10.64 | 0.15 | 0.767 | 430 | 1, 2, 3, 4, 5, 6, 433 | Réponse avec citation non vérifiée |
| Que dit l'article premier du Code du travail ? | retrieval | 10.26 | 0.21 | 1.000 | 1 | 1 | Réponse sourcée, article attendu cité |
| Quelles obligations l'employeur a-t-il envers les agents de l'inspection du travail ? | retrieval | 10.10 | 0.24 | 0.694 | 536, 538 | 538 | Réponse sourcée, article attendu cité |
| Que se passe-t-il si l'employeur ne respecte pas une mise en demeure d'hygiène et de sécurité ? | retrieval | 10.05 | 0.21 | 0.767 | 540, 542 | 300, 540, 542 | Réponse sourcée, article attendu cité |
| Quelles obligations de sécurité et de santé l'employeur a-t-il envers ses salariés ? | retrieval | 9.23 | 0.18 | 0.717 | 24, 281 | 24, 169, 287, 504, 542 | Réponse sourcée, article attendu cité |
| Comment est calculée l'indemnité de licenciement ? | retrieval | 8.41 | 0.15 | 0.788 | 53 | 41, 51, 53, 55, 56, 59, 356 | Réponse avec citation non vérifiée |
| Que dit l'article 32 du Code du travail ? | retrieval | 7.14 | 0.14 | 1.000 | 32 | 32, 154, 156, 274, 275, 277 | Réponse avec citation non vérifiée |
| Pour combien de temps peut-on conclure un CDD à l'ouverture d'une nouvelle entreprise ? | retrieval | 6.45 | 0.17 | 0.604 | 17 | 17, 136, 495 | Réponse sourcée, article attendu cité |
| Qu'est-ce qu'un conflit collectif du travail ? | retrieval | 6.33 | 0.18 | 0.692 | 549 | 549 | Réponse sourcée, article attendu cité |
| Quel est le contenu de l'article 256 ? | retrieval | 6.33 | 0.15 | 1.000 | 256 | 256 | Réponse sourcée, article attendu cité |
| Comment sont calculés les dommages-intérêts en cas de licenciement abusif ? | retrieval | 6.15 | 0.15 | 0.726 | 41 | 41, 301 | Réponse sourcée, article attendu cité |
| L'employeur peut-il licencier une salariée enceinte ? | retrieval | 5.37 | 0.16 | 0.715 | 159 | 159, 160 | Réponse sourcée, article attendu cité |
| Quelle est la durée du congé de maternité ? | retrieval | 5.32 | 0.16 | 0.680 | 152 | 152, 154, 156 | Réponse sourcée, article attendu cité |
| Comment calculer l'impôt sur le revenu au Maroc ? | abstention | 5.29 | 0.17 | 0.556 | — | — | Abstention correcte |
| Quelle est la durée minimale du repos hebdomadaire ? | retrieval | 5.29 | 0.16 | 0.661 | 205 | 206 | Réponse sourcée, autre article cité |
| Dans quels cas le conflit est-il soumis à la commission nationale d'enquête et de conciliation ? | retrieval | 5.08 | 0.24 | 0.743 | 565 | 565, 566 | Réponse sourcée, article attendu cité |
| Dans quel délai l'arbitre doit-il rendre sa décision ? | retrieval | 4.98 | 0.19 | 0.749 | 574 | 574, 578 | Réponse sourcée, article attendu cité |
| Le salarié doit-il être entendu avant d'être licencié ? | retrieval | 4.83 | 0.17 | 0.709 | 62 | 62 | Réponse sourcée, article attendu cité |
| À quel âge un salarié est-il mis à la retraite ? | retrieval | 4.76 | 0.14 | 0.749 | 526 | 53, 526 | Réponse avec citation non vérifiée |
| Quelle amende sanctionne le défaut d'ouverture du registre des mises en demeure ? | retrieval | 4.58 | 0.17 | 0.705 | 547 | 536, 547 | Réponse sourcée, article attendu cité |
| Comment créer une société anonyme au Maroc ? | abstention | 4.51 | 0.14 | 0.515 | — | — | Abstention correcte |
| Dans quel délai faut-il saisir le tribunal après un licenciement contesté ? | retrieval | 4.49 | 0.18 | 0.721 | 65 | 41, 65, 532 | Réponse avec citation non vérifiée |
| Quel est le meilleur moment de l'année pour visiter Marrakech ? | abstention | 4.39 | 0.18 | 0.446 | — | — | Abstention correcte |
| Combien de jours de congé annuel payé acquiert-on par mois de service ? | retrieval | 4.12 | 0.15 | 0.696 | 231 | 231, 235, 238 | Réponse sourcée, article attendu cité |
| À quel âge minimum un mineur peut-il être employé au Maroc ? | retrieval | 4.04 | 0.18 | 0.766 | 143 | 143, 145 | Réponse sourcée, article attendu cité |
| Que prévoit l'article 152 ? | retrieval | 3.92 | 0.13 | 1.000 | 152 | 152 | Réponse sourcée, article attendu cité |
| L'employeur doit-il tenir un registre des mises en demeure ? | retrieval | 3.91 | 0.17 | 0.756 | 536 | 536 | Réponse sourcée, article attendu cité |
| Que doit faire un salarié malade pour justifier son absence ? | retrieval | 3.55 | 0.15 | 0.764 | 271 | 271 | Réponse sourcée, article attendu cité |
| Une mère salariée a-t-elle droit à un repos pour allaiter son enfant ? | retrieval | 3.50 | 0.18 | 0.793 | 161 | 161 | Réponse sourcée, article attendu cité |
| Que prévoit l'article 217 ? | retrieval | 3.39 | 0.17 | 1.000 | 217 | 217 | Réponse sourcée, article attendu cité |
| Quelle est la peine encourue pour vol qualifié ? | abstention | 3.27 | 0.14 | 0.445 | — | — | Abstention correcte |
| Quelles sont les règles du hors-jeu au football ? | abstention | 3.21 | 0.16 | 0.432 | — | — | Abstention correcte |
| Comment l'arbitre est-il désigné en cas de conflit collectif ? | retrieval | 3.01 | 0.25 | 0.672 | 568 | — | Refus à tort (question valide) |
| Quelles sont les conditions pour obtenir un passeport marocain ? | abstention | 2.99 | 0.17 | 0.603 | — | — | Abstention correcte |
| Quelle est la valeur juridique des procès-verbaux dressés par l'inspection du travail ? | retrieval | 2.90 | 0.18 | 0.633 | 539 | 539 | Réponse sourcée, article attendu cité |
| La discrimination salariale entre hommes et femmes est-elle autorisée ? | retrieval | 2.80 | 0.16 | 0.755 | 346 | 346 | Réponse sourcée, article attendu cité |
| À partir de combien de salariés un comité de sécurité et d'hygiène est-il obligatoire ? | retrieval | 2.71 | 0.16 | 0.692 | 336 | — | Réponse sans aucune citation |
| Le salarié appelé au service militaire est-il indemnisé pour son congé annuel non pris ? | retrieval | 2.65 | 0.17 | 0.784 | 256 | 256 | Réponse sourcée, article attendu cité |
| Le service militaire suspend-il le contrat de travail ? | retrieval | 2.54 | 0.18 | 0.654 | 32 | 32 | Réponse sourcée, article attendu cité |
| Dans quel délai peut-on contester une décision d'arbitrage ? | retrieval | 2.44 | 0.17 | 0.716 | 577 | 577 | Réponse sourcée, article attendu cité |
| Combien d'heures par mois un délégué des salariés a-t-il pour exercer ses fonctions ? | retrieval | 2.41 | 0.16 | 0.712 | 456 | 456 | Réponse sourcée, article attendu cité |
| Quelle est la durée de la période d'essai pour un cadre en contrat à durée indéterminée ? | retrieval | 2.38 | 0.35 | 0.783 | 14 | 14 | Réponse sourcée, article attendu cité |
| Quelle est la durée légale du travail dans les activités non agricoles ? | retrieval | 2.37 | 0.14 | 0.737 | 184 | 184 | Réponse sourcée, article attendu cité |
| Un salarié appelé au service militaire retrouve-t-il son poste au retour ? | retrieval | 2.25 | 0.16 | 0.696 | 510 | 510 | Réponse sourcée, article attendu cité |
| Quelle est la procédure pour divorcer au Maroc ? | abstention | 2.15 | 0.15 | 0.515 | — | — | Abstention correcte |
| Peut-on employer un mineur de moins de 18 ans dans les mines ? | retrieval | 2.09 | 0.18 | 0.718 | 179 | 179 | Réponse sourcée, article attendu cité |
| Quelle est la durée maximale d'une mission d'intérim ? | retrieval | 2.08 | 0.16 | 0.596 | 500 | — | Réponse sans aucune citation |
| À partir de combien de salariés faut-il créer un comité d'entreprise ? | retrieval | 2.07 | 0.15 | 0.674 | 464 | 464 | Réponse sourcée, article attendu cité |
| Est-il permis de faire travailler les salariés pendant les jours de fête payés ? | retrieval | 1.98 | 0.15 | 0.714 | 217 | 217 | Réponse sourcée, article attendu cité |
| Qui est chargé de l'inspection du travail ? | retrieval | 1.90 | 0.16 | 0.679 | 530 | 538 | Réponse sourcée, autre article cité |
| Combien de jours d'absence a-t-on pour son propre mariage ? | retrieval | 1.87 | 0.15 | 0.708 | 274 | 274 | Réponse sourcée, article attendu cité |
| Combien de jours de congé un salarié a-t-il à l'occasion d'une naissance ? | retrieval | 1.85 | 0.17 | 0.771 | 269 | 269 | Réponse sourcée, article attendu cité |
| À partir de quelle ancienneté la prime d'ancienneté est-elle due, et à quel taux ? | retrieval | 1.73 | 0.17 | 0.733 | 350 | 350 | Réponse sourcée, article attendu cité |
| Faut-il une autorisation pour recruter un salarié étranger ? | retrieval | 1.68 | 0.16 | 0.728 | 516 | 516 | Réponse sourcée, article attendu cité |
| Le harcèlement sexuel commis par l'employeur est-il une faute grave ? | retrieval | 1.18 | 0.15 | 0.716 | 40 | 39, 40 | Réponse sourcée, article attendu cité |
| Quelle est la recette du couscous royal ? | abstention | 0.14 | 0.14 | 0.307 | — | — | Abstention correcte |
| Quelle est la capitale de la France ? | abstention | 0.13 | 0.13 | 0.336 | — | — | Abstention correcte |
