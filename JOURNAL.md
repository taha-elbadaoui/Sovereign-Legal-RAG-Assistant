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
