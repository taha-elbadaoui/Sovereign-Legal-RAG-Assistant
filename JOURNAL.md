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
