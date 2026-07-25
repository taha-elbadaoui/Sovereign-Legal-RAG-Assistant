# Mesures de performance — Assistant juridique RAG

Jeu de référence : **32** questions dans le périmètre, **5** hors périmètre. Modèle local : `mistral:7b`.

> Toutes les valeurs de ce document sont produites par `python eval/run_measures.py` — aucune n'est saisie à la main.

## 1. Latence

| Étape | Médiane | Moyenne | p90 | Max |
|---|---|---|---|---|
| Recherche (toutes questions) | 0.15 s | 0.16 s | 0.17 s | 0.44 s |
| Génération LLM | 4.19 s | 4.55 s | 7.82 s | 14.84 s |
| **Total (avec génération)** | **4.36 s** | 4.72 s | 7.97 s | 15.01 s |
| **Total (abstention pré-LLM)** | **0.14 s** | 0.14 s | 0.14 s | 0.14 s |

Le garde-fou d'abstention divise le temps de réponse par **31×** sur les questions hors périmètre (0.14 s contre 4.36 s) : le modèle n'est pas appelé du tout.

La recherche représente environ **3 %** du temps total ; le reste est l'inférence du modèle local.

![Répartition de la latence](figures/latence-repartition.svg)

![Distribution du temps de réponse](figures/latence-distribution.svg)

## 2. Classement des réponses

| Catégorie | Nombre | Part |
|---|---|---|
| Réponse sourcée, article attendu cité | 23 | 62 % |
| Réponse sourcée, autre article cité | 3 | 8 % |
| Réponse avec citation non vérifiée | 3 | 8 % |
| Réponse sans aucune citation | 1 | 3 % |
| Refus à tort (question valide) | 2 | 5 % |
| Abstention correcte | 5 | 14 % |

![Taxonomie des résultats](figures/taxonomie-resultats.svg)

### Ce que ces catégories veulent dire

- **Réponse sourcée, article attendu cité** — le système répond et cite l'article de référence prévu par le jeu de test.
- **Réponse sourcée, autre article cité** — réponse fondée sur un article voisin. Souvent défendable en droit (p. ex. citer 337 au lieu de 336), à trancher au cas par cas.
- **Citation non vérifiée** — un numéro cité n'était pas dans le contexte fourni. Dans la pratique il s'agit surtout de **renvois internes** (« …prévu par l'article N ci-dessous ») repris depuis le texte d'un article bien fourni. Signal de vigilance, **pas** une hallucination démontrée.
- **Refus à tort** — question légitime refusée : c'est le coût d'une abstention trop stricte.
- **Répond alors qu'il devrait s'abstenir** — le cas le plus grave : le système produit une réponse sur un sujet absent du corpus.

## 3. Garde-fou d'abstention

![Séparation des scores](figures/separation-abstention.svg)

- Questions dans le périmètre : score de **0.596** à **0.793**
- Questions hors périmètre : score de **0.307** à **0.515**
- Seuil retenu : **0.42**

Le seuil ne cherche pas à séparer le droit du travail des autres domaines juridiques — il ne filtre que la bande clairement non pertinente. Les questions juridiques hors corpus passent le seuil et sont rattrapées par l'abstention au niveau du prompt.

## 4. Fiabilité — indicateurs

![Indicateurs de fiabilité](figures/fiabilite-synthese.svg)

## 5. Limite de mesure assumée

La vérification des citations contrôle qu'un article cité **figurait dans le contexte fourni** — pas qu'il **dise réellement** ce que la réponse lui attribue. Une réponse citant un article réel en en déformant le contenu est comptée ici comme sourcée. Détecter ce cas demanderait une vérification d'implication (entailment) ou une relecture humaine ; c'est hors périmètre du stage et documenté comme tel.

## 6. Détail par question

| Question | Type | Total (s) | Recherche (s) | Score | Attendu | Cité | Classement |
|---|---|---|---|---|---|---|---|
| Quelles sont les fautes graves pouvant justifier le licenciement d'un salarié ? | retrieval | 15.01 | 0.17 | 0.781 | 39 | 39, 40, 160, 293 | Réponse sourcée, article attendu cité |
| Quelles obligations de sécurité et de santé l'employeur a-t-il envers ses salariés ? | retrieval | 11.23 | 0.17 | 0.717 | 24, 281 | 24, 169, 287, 504, 542 | Réponse sourcée, article attendu cité |
| Quelles catégories de salariés sont régies par des statuts spéciaux ? | retrieval | 8.61 | 0.15 | 0.695 | 3 | 4, 11 | Réponse sourcée, autre article cité |
| Comment est calculée l'indemnité de licenciement ? | retrieval | 7.97 | 0.15 | 0.788 | 53 | 53, 55 | Réponse sourcée, article attendu cité |
| À partir de combien de salariés doit-on élire des délégués des salariés ? | retrieval | 7.95 | 0.15 | 0.767 | 430 | 433 | Réponse sourcée, autre article cité |
| Quelle est la durée de la période d'essai pour un cadre en contrat à durée indéterminée ? | retrieval | 7.89 | 0.44 | 0.783 | 14 | 14 | Réponse sourcée, article attendu cité |
| Quelle est la durée minimale du repos hebdomadaire ? | retrieval | 6.68 | 0.15 | 0.661 | 205 | 206 | Réponse sourcée, autre article cité |
| Quelle est la durée du congé de maternité ? | retrieval | 6.28 | 0.15 | 0.680 | 152 | 152, 154, 156, 269 | Réponse sourcée, article attendu cité |
| À quel âge un salarié est-il mis à la retraite ? | retrieval | 5.57 | 0.15 | 0.749 | 526 | 53, 526 | Réponse avec citation non vérifiée |
| L'employeur peut-il licencier une salariée enceinte ? | retrieval | 5.56 | 0.15 | 0.715 | 159 | 159, 160 | Réponse sourcée, article attendu cité |
| Pour combien de temps peut-on conclure un CDD à l'ouverture d'une nouvelle entreprise ? | retrieval | 5.46 | 0.16 | 0.604 | 17 | 17 | Réponse sourcée, article attendu cité |
| Le salarié doit-il être entendu avant d'être licencié ? | retrieval | 5.12 | 0.15 | 0.709 | 62 | 62 | Réponse sourcée, article attendu cité |
| Combien de jours de congé annuel payé acquiert-on par mois de service ? | retrieval | 5.04 | 0.15 | 0.696 | 231 | 231, 238 | Réponse sourcée, article attendu cité |
| Dans quel délai faut-il saisir le tribunal après un licenciement contesté ? | retrieval | 4.85 | 0.16 | 0.721 | 65 | 41, 65, 532 | Réponse avec citation non vérifiée |
| Que doit faire un salarié malade pour justifier son absence ? | retrieval | 4.62 | 0.15 | 0.764 | 271 | 271 | Réponse sourcée, article attendu cité |
| Comment sont calculés les dommages-intérêts en cas de licenciement abusif ? | retrieval | 4.41 | 0.15 | 0.726 | 41 | 41, 532 | Réponse avec citation non vérifiée |
| Peut-on employer un mineur de moins de 18 ans dans les mines ? | retrieval | 4.39 | 0.15 | 0.718 | 179 | 179, 180 | Refus à tort (question valide) |
| À quel âge minimum un mineur peut-il être employé au Maroc ? | retrieval | 4.36 | 0.17 | 0.766 | 143 | 143, 145 | Réponse sourcée, article attendu cité |
| Comment créer une société anonyme au Maroc ? | abstention | 4.25 | 0.15 | 0.515 | — | — | Abstention correcte |
| Quelle est la peine encourue pour vol qualifié ? | abstention | 3.85 | 0.16 | 0.445 | — | — | Abstention correcte |
| Une mère salariée a-t-elle droit à un repos pour allaiter son enfant ? | retrieval | 3.75 | 0.16 | 0.793 | 161 | 161 | Réponse sourcée, article attendu cité |
| À partir de combien de salariés un comité de sécurité et d'hygiène est-il obligatoire ? | retrieval | 3.58 | 0.16 | 0.692 | 336 | 337 | Refus à tort (question valide) |
| Combien d'heures par mois un délégué des salariés a-t-il pour exercer ses fonctions ? | retrieval | 3.02 | 0.16 | 0.712 | 456 | 456 | Réponse sourcée, article attendu cité |
| La discrimination salariale entre hommes et femmes est-elle autorisée ? | retrieval | 3.00 | 0.15 | 0.755 | 346 | 346 | Réponse sourcée, article attendu cité |
| Quelle est la durée légale du travail dans les activités non agricoles ? | retrieval | 2.58 | 0.16 | 0.737 | 184 | 184 | Réponse sourcée, article attendu cité |
| Un salarié appelé au service militaire retrouve-t-il son poste au retour ? | retrieval | 2.49 | 0.15 | 0.696 | 510 | 510 | Réponse sourcée, article attendu cité |
| Quelle est la durée maximale d'une mission d'intérim ? | retrieval | 2.29 | 0.15 | 0.596 | 500 | — | Réponse sans aucune citation |
| À partir de combien de salariés faut-il créer un comité d'entreprise ? | retrieval | 2.25 | 0.15 | 0.674 | 464 | 464 | Réponse sourcée, article attendu cité |
| Quelle est la procédure pour divorcer au Maroc ? | abstention | 2.24 | 0.15 | 0.515 | — | — | Abstention correcte |
| Est-il permis de faire travailler les salariés pendant les jours de fête payés ? | retrieval | 2.13 | 0.15 | 0.714 | 217 | 217 | Réponse sourcée, article attendu cité |
| Combien de jours de congé un salarié a-t-il à l'occasion d'une naissance ? | retrieval | 1.92 | 0.15 | 0.771 | 269 | 269 | Réponse sourcée, article attendu cité |
| Combien de jours d'absence a-t-on pour son propre mariage ? | retrieval | 1.86 | 0.15 | 0.708 | 274 | 274 | Réponse sourcée, article attendu cité |
| Faut-il une autorisation pour recruter un salarié étranger ? | retrieval | 1.78 | 0.17 | 0.728 | 516 | 516 | Réponse sourcée, article attendu cité |
| À partir de quelle ancienneté la prime d'ancienneté est-elle due, et à quel taux ? | retrieval | 1.72 | 0.17 | 0.733 | 350 | 350 | Réponse sourcée, article attendu cité |
| Le harcèlement sexuel commis par l'employeur est-il une faute grave ? | retrieval | 1.33 | 0.16 | 0.716 | 40 | 39, 40 | Réponse sourcée, article attendu cité |
| Quelle est la recette du couscous royal ? | abstention | 0.14 | 0.14 | 0.307 | — | — | Abstention correcte |
| Quelle est la capitale de la France ? | abstention | 0.13 | 0.13 | 0.336 | — | — | Abstention correcte |
