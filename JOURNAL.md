# Working structure

```
sovereign-legal-rag/
│
├── data/
│   ├── raw/                           # Documents originaux non modifiés
│   │   ├── code-du-travail.pdf
│   │   └── القانون رقم 65.99 المتعلق بمدونة الشغل.pdf
│   └── processed/                     # Corpus structuré et découpé (Mission 1)
│       └── corpus_chunks.jsonl        # Ton fichier de chunks final prêt à être indexé
│
├── docs/                              # Analyses, arbitrages et planification
│   ├── comparaison-code-du-travail-FR-AR.md
│   ├── comparaison-code.md
│   ├── Sovereign-Legal-RAG-8-Week-Plan-v2.md
│   └── Tech-Stack-Decision-Rationale-v2.md
│
├── eval/                              # Dataset et scripts d'évaluation (Mission 3)
│   ├── reference_qa.jsonl             # Tes 30 à 50 couples Q&A "Gold"
│   └── run_eval.py                    # Script de calcul des métriques (Recall@k, MRR...)
│
├── src/                               # Code source du pipeline RAG
│   ├── __init__.py
│   ├── parser.py                      # Extraction du texte & Structuration (Week 1-2)
│   ├── database.py                    # Gestion de la base ChromaDB (Week 3)
│   ├── retriever.py                   # Recherche Dense (BGE-M3) + Lexicale (BM25) (Week 3/5)
│   ├── generator.py                   # Prompts Ollama, gestion de l'abstention & citations (Week 4)
│   └── app.py                         # Point d'entrée de l'application (CLI ou Streamlit)
│
├── .gitignore                         # Pour exclure les environnements virtuels (.venv/) et les DB locales
├── JOURNAL.md                         # Ton carnet de bord quotidien (Laissé à la racine pour un accès rapide)
├── README.md                          # Guide d'installation et d'exécution du projet
└── requirements.txt                   # Dépendances Python épinglées
```

---

## 2026-07-02 — Semaine 1 : extraction brute + inspection

**Fait :**
- Écriture d'une première version de `src/parser.py` : ouverture du PDF `data/raw/code-du-travail.pdf` avec PyMuPDF (`fitz`), extraction du texte page par page.
- Bug rencontré et corrigé : ouverture accidentelle de `PDF_PATH` en mode écriture (`"w"`) au lieu du fichier de sortie → risque d'écraser la source. Corrigé en séparant clairement le chemin de lecture (PDF) du chemin d'écriture (`output.txt`).
- Bug rencontré et corrigé : caractères accentués corrompus en sortie (`�`, soit U+FFFD) car l'écriture ne précisait pas `encoding="utf-8"`. Corrigé — les accents (é, è, à, ç, œ...) sortent maintenant correctement.
- Export du texte brut vers `output.txt` (7810 lignes, ~372 Ko) pour inspection manuelle.

**Constaté à l'inspection :**
- La structure "Article" est très régulière : 588 occurrences de `Article premier` / `Article N`, chacune seule sur sa ligne, sans variante détectée (`bis`, sous-articles du type `9-1`, etc. — aucun trouvé pour l'instant).
- Le premier article (`Article premier`) commence à la ligne 379 du texte extrait. Tout ce qui précède (Dahir de promulgation, Préface royale) est du texte hors-corpus légal à traiter séparément (probablement à exclure du découpage par article).
- Parasites de pagination détectés : motif répété à chaque saut de page, forme ` -\n<numéro>\n - `. À nettoyer par regex avant le découpage par article.

**Prochaine étape (toujours Semaine 1 / début Semaine 2) :**
- Écrire le découpage par article avec `re.split()` + groupe capturant sur le motif `Article (?:premier|\d+)`.
- Décider du sort du texte avant `Article premier` (garder à part vs. jeter).
- Nettoyer la pagination avant ou après le découpage.
- Faire une vérification manuelle sur ~10 articles extraits vs. le PDF source (fidélité).

---

## 2026-07-03 — Semaine 1 : découpage par article réussi

**Fait :**
- Découpage du texte complet en articles avec `re.split(r"(^Article\s(?:premier|\d+))", full_text, flags=re.MULTILINE)`. Le groupe capturant `(...)` conserve les en-têtes d'article dans la liste `parts`, qui alterne alors : [avant-propos, "Article premier", corps, "Article 2", corps, ...].
- L'ancre `^` + le drapeau `re.MULTILINE` garantissent qu'on ne matche que les vrais en-têtes en début de ligne, pas le mot « article » dans les renvois au fil du texte.
- Découverte : la hiérarchie (`Livre` / `Titre` / `Chapitre` / `Section`) est bien présente dans le texte extrait, en lignes autonomes → exploitable pour les métadonnées en Semaine 2.
- Nettoyage du **back matter** : la table des matières se retrouvait collée au corps du dernier article (Article 589), faute d'« Article 590 » sur lequel couper. Séparée via `parts[-1].split("TABLE DES MATIÈRES")` → `temp[0]` (texte réel de l'article) reste dans `parts[-1]`, `temp[1]` (table des matières) ajouté comme **nouvelle entrée finale** de la liste.
- `~1179` éléments dans `parts` (1 avant-propos + 588×2 + 1 table des matières).

**Bugs / confusions traversés (pour mémoire) :**
- Erreur classique : passer `re.MULTILINE` en 3e argument positionnel de `re.split` → c'est `maxsplit`, pas `flags`. Corrigé avec `flags=re.MULTILINE`.
- Tentatives répétées de faire supprimer la table des matières *par le regex de découpage* : `re.split` ne supprime jamais, il ne fait que découper et tout conserver. La suppression/mise à part est une étape distincte sur `parts[-1]`.

**Hypothèses fragiles à surveiller (Semaine 7 durcissement) :**
- Saut des 10 premières pages codé en dur (page 10 = `Article premier` pour *cette* version consolidée 2011). Une autre version PDF décalerait ce seuil. À terme : détecter `Article premier` dans le texte plutôt qu'un numéro de page.
- `temp[1]` suppose que `TABLE DES MATIÈRES` existe dans le dernier élément ; sinon `IndexError`.

**Prochaine étape (Semaine 2 — cœur de la Mission 1) :**
- Transformer `parts` (liste plate label/corps) en liste structurée `[{"article_number": ..., "text": ...}, ...]` via une boucle qui parcourt la liste 2 par 2 (`range(1, len(parts), 2)`).
- Attacher les métadonnées de hiérarchie (`livre`, `titre`, `chapitre`, `section`) — attention : les en-têtes apparaissent à la frontière du *mauvais* article, à réattribuer.
- Nettoyer la pagination ` -\n<numéro>\n - ` et normaliser les retours à la ligne en milieu de phrase (artefacts PyMuPDF).
- Sérialiser en JSONL (`data/processed/corpus_chunks.jsonl`), un chunk par ligne, de façon déterministe.
- Vérification manuelle ~10 articles vs. PDF source.

---

## 2026-07-07 — Semaine 2 : structuration en liste d'articles

**Fait :**
- Transformation de la liste plate `parts` en liste structurée `articles` = `[{"article_number": ..., "article_text": ...}, ...]` via une boucle `for i in range(1, len(parts)-1, 2)` (parcours 2 par 2 : label puis corps).
- Normalisation du numéro : `"Article premier"` → `article_number = "1"` (via une branche `if "premier" in parts[i]`), tous les autres via `parts[i].replace("Article ", "")`. **Choix de conception :** `article_number` stocké en **chaîne** (`"1"`, `"2"`, `"152"`) — pas d'`int` — pour la cohérence des comparaisons/citations en aval (Semaine 5-6).
- Le `range(1, len(parts)-1, 2)` s'arrête avant la table des matières (dernier élément appendé), évitant l'`IndexError` sur `parts[i+1]`.
- **Résultat vérifié : `len(articles) == 588`.** `articles[0]` = Article 1, `articles[-1]` = Article 589. ✅

**Bugs traversés (pour mémoire) :**
- `parts[i].contains("premier")` → les chaînes Python n'ont pas de `.contains()`. Utiliser l'opérateur `in` : `"premier" in parts[i]`.
- Double `append` pour l'article premier (branche `if` + `append` inconditionnel en dessous) → corrigé avec `else`.

**Constaté (à nettoyer — prochaine sous-étape) :**
- Le champ `article_text` contient encore le bruit d'extraction PyMuPDF : retours à la ligne en milieu de phrase (un `\n` par ligne visuelle du PDF), marqueurs de pagination ` -\n<numéro>\n - `, espaces en début/fin, codes parasites (`\n0305111201` en fin d'Article 589). NB : les `\n` vus à l'écran via `print(dict)` sont l'affichage `repr` ; le vrai problème est leur présence dans les données, pas l'affichage.

**Prochaine étape :**
- Normalisation du texte (`re.sub`) : supprimer les marqueurs de pagination, réduire les suites d'espaces/retours à la ligne en un seul espace, `strip()` les bords.
- Puis : métadonnées de hiérarchie, sérialisation JSONL, vérification manuelle ~10 articles.

---

## 2026-07-20 — Semaine 3 : hiérarchie, nettoyage, JSONL — S2 terminée

**Fait :**
- Normalisation du texte : suppression des marqueurs de pagination, réduction des retours à la ligne PyMuPDF (un `\n` par ligne visuelle) en un seul espace, `strip()` des bords.
- Métadonnées de hiérarchie (`livre`, `titre`, `chapitre`, `section`) attachées à chaque article via `HEADER_RE` + un dictionnaire `hierarchy` mis à jour au fil du texte (`RESET_BELOW` : un nouveau `Titre` réinitialise `chapitre`/`section`, etc.). Amorçage depuis l'avant-propos (`parts[0]`) pour que l'Article 1 hérite bien de `Livre préliminaire` / `Titre premier`.
- Sérialisation en JSONL déterministe : `data/processed/corpus_chunks.jsonl`, un article par ligne, schéma `{article_number, article_text, amende_2021, livre, titre, chapitre, section}` identique sur les 589 lignes.
- Patch de contenu légal sourcé sur les articles 32 et 256 : tous deux abrogés en 2007 (loi 48-06, suppression du service militaire) et donc vides ou quasi-vides dans ce PDF FR de 2011 ; texte de remplacement 2021 (loi 02.21) injecté, déjà vérifié dans `docs/comparaison-code-du-travail-FR-AR.md`. Champ `amende_2021` ajouté à **tous** les articles (`False` par défaut) pour que la déviation reste visible et traçable dans la donnée elle-même.
- Vérification systématique (script, pas à l'œil) sur 5 catégories : intégrité de séquence (1→589, doublons, trous), textes anormalement courts, suites de 5+ chiffres suspectes, fragments d'en-tête oubliés dans le corps, articles sans hiérarchie.

**Bugs trouvés et corrigés (via le sweep + vérification manuelle) :**
- **Numéros d'article corrompus par un chiffre de renvoi de bas de page collé** (`"33450"` au lieu de `"334"`, `"25635"` au lieu de `"256"`) : PyMuPDF ne préserve pas la mise en exposant, donc un appel de note collé à un numéro d'article dans le PDF ressort comme une seule suite de chiffres sans séparateur. Corrigé en plafonnant le regex de découpage à `\d{1,3}` (aucun article ne dépasse 589, donc 4+ chiffres = numéro + reliquat de note).
- **Article 135 absent du corpus** (588 au lieu de 589) : un espace parasite avant `Article 135` sur sa propre ligne cassait l'ancre stricte `^Article`, donc son contenu était silencieusement absorbé dans le corps de l'Article 134. Trouvé en scannant les trous de séquence, pas en relisant à l'œil. Corrigé avec `[ \t]*` avant `Article` dans le regex de découpage.
- **Titres de hiérarchie repliés sur 2 ou 3 lignes dans le PDF** (32 cas trouvés, dont 5 sur 3 lignes, ex. `Chapitre VII : Le Conseil supérieur de la promotion de\nl'emploi et les conseils régionaux et provinciaux de la\npromotion de l'emploi.`) : `HEADER_RE` ne capturait que la première ligne visuelle, donc (a) les champs `livre`/`titre`/`chapitre`/`section` restaient tronqués pour **tous** les articles sous ce titre jusqu'au suivant du même niveau, et (b) la ou les lignes de continuation fuyaient dans le corps de l'article adjacent (ex. Article 521 se terminait par `"...articles 518 et 519. l'emploi et les conseils régionaux et provinciaux de la promotion de l'emploi."`). Trouvé en comparant le corpus parsé au PDF brut pendant la vérification manuelle (Article 550), puis quantifié par script avant de corriger. Corrigé en étendant `HEADER_RE` pour continuer à consommer les lignes suivantes tant qu'elles ne commencent pas elles-mêmes par `Livre`/`Titre`/`Chapitre`/`Section`/`Article`.
- Cohérence de schéma : `amende_2021` ajouté par défaut à tous les articles dès leur création (pas seulement aux deux patchés), pour éviter tout code aval qui devrait gérer une clé absente.

**Limites connues, non corrigées (bruit mineur, dans la prose, pas dans les champs structurants) :**
- Articles 73 et 76 : un chiffre de renvoi de bas de page reste collé à une référence d'article *dans* le texte courant (`"l'article 109814"` = « l'article 1098 » + note « 14 »), pas au numéro d'article lui-même — non corrigé.
- Article 589 : un numéro de code-barres/impression parasite (`0305111201`) en toute fin de texte — non corrigé.

**Vérification manuelle (fidélité PDF, échantillon en cours) :**
- Articles 1, 32, 256, 327, 334, 521, 522, 550, 551 vérifiés (via le débogage des bugs ci-dessus).
- Restent à échantillonner par Taha : 152, 300, 400, 500, 588, 589.

**Prochaine étape (S3) :**
- Premier pipeline RAG bout-en-bout : embeddings BGE-M3, base Chroma, index BM25, fusion RRF, génération via Ollama, citations systématiques.

---

## 2026-07-24 — Semaine 3 : premier pipeline RAG bout-en-bout (S3)

**Contexte :** demande de démonstration de l'encadrant le jour même (16h). Environnement RAG construit de zéro dans la foulée : Ollama installé, modèle `mistral:7b` téléchargé, dépendances Python (`chromadb`, `sentence-transformers`, `rank_bm25`, `ollama`) installées dans le `.venv`.

**Fait :**
- `src/database.py` : embarque les 589 articles du corpus avec BGE-M3 (embeddings multilingues, local, aucun appel API) et les indexe dans une base vectorielle Chroma persistante (`data/chroma/`), avec la hiérarchie (livre/titre/chapitre/section) et `amende_2021` comme métadonnées filtrables.
- `src/retriever.py` : recherche hybride — index lexical BM25 (mots-clés exacts) + recherche dense (similarité sémantique via l'index Chroma) — fusionnés par Reciprocal Rank Fusion (RRF). Choix motivé : le vocabulaire juridique mélange formulations formelles (le texte de loi) et casual (les questions des utilisateurs), donc aucune des deux méthodes seule ne suffit ; RRF combine les deux sans avoir à normaliser des échelles de score incompatibles (BM25 non borné vs. cosinus 0-1).
- `src/generator.py` : génération ancrée via Ollama/Mistral 7B local. Le prompt système impose : réponse strictement basée sur les articles fournis, citation systématique des numéros d'article, abstention explicite si le corpus fourni ne permet pas de répondre, pas de conseil juridique personnalisé.
- `eval/questions-test.md` : jeu de test manuel de 15 questions/réponses attendues (avec article source), vérifiées une à une contre le texte réel du corpus, incluant un test d'abstention volontaire (question hors périmètre du Code du travail).
- Premier test bout-en-bout réel : "Quelle est la durée du congé annuel payé ?" → réponse correctement ancrée, citations exactes (articles 232, 235, 240, 241), aucune invention.

**Limite trouvée et documentée (pas corrigée aujourd'hui, décision volontaire) :**
- Sur ce même test, l'Article 231 (règle de base : un jour et demi par mois de service) n'est pas ressorti dans le top 5 fusionné, alors qu'il est 2e en recherche dense pure. Diagnostic : BM25 ne le trouve pas du tout dans son top 20 (son score est dilué par la longueur de l'article), donc RRF ne lui attribue de crédit que via une seule méthode — les articles présents dans les deux listes, même à un rang moins bon individuellement, l'emportent par effet de consensus. Augmenter `k` jusqu'à 10 ne corrige pas le problème (vérifié). C'est une limite connue et documentée de RRF, pas un bug — la correction prévue est le reranking par cross-encodeur (S5), qui rescorera précisément les candidats fusionnés au lieu de se fier au seul rang de fusion.
- L'abstention par seuil *avant* l'appel au LLM (F5 du plan) n'est pas encore implémentée — seule l'abstention au niveau du prompt l'est. Un seuil non calibré risquerait de refuser à tort des questions valides ; la calibration nécessite le jeu de référence formel (S5/S6).

**Prochaine étape (S4/S5) :**
- Compléter le jeu de référence formel (`eval/reference_qa.jsonl`, 30-50 questions) pour pouvoir calibrer le seuil d'abstention pré-LLM.
- Reranking par cross-encodeur pour corriger la limite RRF ci-dessus.
- Script d'évaluation (Recall@k, MRR) comparant dense seul / BM25 seul / hybride.

---

## 2026-07-24 (soir) — S4 à S6 : abstention, vérification, évaluation, interface

Séance de finalisation du périmètre Code du travail : abstention pré-LLM, vérification des citations, jeu de référence, évaluation mesurée, et interface web de type conversationnel.

**Fait :**
- **`app.py` — orchestrateur** partagé (utilisé à l'identique par la CLI et l'interface web) : recherche → garde-fou d'abstention → génération → vérification des citations → affichage avec avertissement.
- **Abstention pré-LLM (F5)** : ajout d'un signal de score = similarité cosinus dense maximale (calculée par produit scalaire sur embeddings normalisés, donc indépendante de la métrique de distance de Chroma). Si le meilleur score < seuil, le LLM n'est pas appelé.
- **Vérification des citations (F6)** : après génération, extraction des numéros d'article cités par le modèle (regex) et contrôle qu'ils figurent bien dans le contexte fourni. Tout numéro cité mais absent est signalé (« citation non vérifiée »).
- **Reranking (F9)** : cross-encodeur `bge-reranker-v2-m3` en option (désactivé par défaut, chargé paresseusement pour ne pas imposer le téléchargement de ~2.3 Go).
- **`eval/reference_qa.jsonl`** : 32 questions de recherche (avec article(s) de référence, vérifiés contre le texte réel) + 5 questions d'abstention.
- **`eval/run_eval.py`** : calcul Recall@k et MRR pour dense seul / BM25 seul / hybride, sans LLM (mesure la recherche seule).
- **`streamlit_app.py`** : interface web conversationnelle (type ChatGPT) — historique, exemples cliquables, réponse + articles sources dépliables (avec chemin hiérarchique et marque « cité »), avertissement de citations non vérifiées, note de souveraineté. Modèles chargés une fois via `@st.cache_resource`.
- **Durcissement** : gestion d'erreur si Ollama est injoignable (message clair au lieu d'un crash) ; sortie CLI forcée en UTF-8 (les consoles Windows en cp1252 plantaient sur les accents / symboles).

**Calibration du seuil d'abstention (mesurée, pas devinée) :**
- Questions dans le périmètre (droit du travail) : similarité **0.60 – 0.79**.
- Questions purement non juridiques (cuisine, géographie) : **0.31 – 0.35**.
- Questions d'un **autre domaine juridique** (famille, pénal, commercial) : **0.47 – 0.52** — plus élevées car elles partagent le vocabulaire juridique français.
- Conclusion : un seuil unique **ne peut pas** séparer le droit du travail des autres domaines juridiques, et **ne doit pas** essayer — quand le corpus sera étendu à d'autres codes, ces questions deviendront légitimes. Le seuil (**0.42**) ne filtre donc que la bande clairement non pertinente ; les questions juridiques hors corpus passent et sont rattrapées par l'abstention au niveau du prompt (le LLM voit que les articles retrouvés ne répondent pas). Vérifié en direct : « recette du couscous » → abstention pré-LLM ; « procédure de divorce » → passe le seuil mais le LLM s'abstient correctement.

**Résultat d'évaluation (Recall@5 / MRR, 32 questions) — constat honnête :**

| Méthode | Recall@5 | MRR |
|---|---|---|
| Dense seul | **0.969** | **0.891** |
| BM25 seul | 0.781 | 0.628 |
| Hybride (RRF) | 0.875 | 0.794 |

- **Sur ce jeu (questions en langage naturel), la recherche dense seule dépasse l'hybride.** Les questions du citoyen sont des reformulations, ce qui favorise le sémantique ; RRF dilue le bon classement dense en y mêlant le classement BM25 plus faible. Ce n'est pas un échec mais un **arbitrage mesuré** : l'hybride prendrait l'avantage sur des requêtes à tokens exacts (numéros d'article, « Loi 65-99 »). Exactement le type de décision que l'évaluation doit éclairer (cf. plan §4.3). Prochain levier à tester : le reranking (S5).

**Limite connue (notée, non corrigée) :**
- La vérification des citations signale aussi les **renvois internes** : si un article cité contient « …fixé par l'article 356 ci-dessous », le modèle peut répéter « article 356 », signalé comme non vérifié même s'il n'est pas présenté comme source. Comportement conservateur (mieux vaut signaler que manquer) ; raffinement possible : distinguer source citée vs renvoi mentionné.

**Prochaine étape (avec l'encadrant) :**
- Extension à un second code (Code de la famille pressenti — cité dans l'offre, très consulté par le citoyen) : preuve que l'architecture généralise. Nécessite un identifiant de code (les numéros d'article ne sont plus uniques entre codes).
- Couche multilingue FR / EN / AR (darija différée : pas d'orthographe standardisée, fort code-switching, peu de données).
