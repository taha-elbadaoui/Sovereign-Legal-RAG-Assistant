# Assistant Juridique RAG Souverain — Plan d'action & état d'avancement

**Projet :** Assistant conversationnel (RAG) sur le droit du travail marocain (Loi n° 65‑99 — Code du travail), français d'abord, avec citation obligatoire des sources et abstention explicite hors périmètre.
**Cadre :** Stage — Pulsaride Solutions · durée : 8 semaines · démarrage : 1er juillet 2026.
**Contrainte de conception :** local / open‑source privilégié (souveraineté des données).

---

## 1. Objectif et principe

L'objectif est un assistant capable, à partir d'une question en langage naturel, de :
1. **retrouver** les articles pertinents du Code du travail,
2. **générer** une réponse fondée *uniquement* sur ces articles,
3. **citer** systématiquement le ou les numéros d'articles utilisés,
4. **s'abstenir** explicitement lorsque la question est hors périmètre ou sans réponse dans le texte.

Le système relève de la **restitution d'information juridique**, et non de l'interprétation ou du conseil juridique personnalisé. Chaque réponse est accompagnée d'un avertissement rappelant ce périmètre.

---

## 2. Périmètre du stage

| | Engagement |
|---|---|
| **Mission 1** | Constitution d'un corpus structuré, reproductible, au niveau de l'article, avec métadonnées. |
| **Mission 2** | Pipeline RAG fonctionnel : question → articles retrouvés → réponse sourcée, sur modèle local. |
| **Mission 3** | Évaluation réelle : jeu de questions/réponses de référence, métriques de recherche, correction manuelle, analyse d'erreurs. |
| **Mission 4 (optionnelle)** | Volet multilingue (arabe / darija) via une **couche de traduction** greffée sur le système français — traité comme expérimentation documentée en fin de stage, si le cœur est solide. |



---

## 3. Stack technique retenue

| Couche | Choix | Justification |
|---|---|---|
| Langage / env. | Python 3.11 + `venv` | Stabilité, écosystème mature. |
| Extraction PDF | **PyMuPDF** (`fitz`), `pdfplumber` en secours | Rapide, robuste sur les accents français. |
| Embeddings | **BGE‑M3** (`sentence-transformers`) | Multilingue (FR + AR), fort en recherche, exécution locale. |
| Base vectorielle | **Chroma** (persistante) | Simple, filtrage par métadonnées, persistance native. |
| Recherche lexicale | **`rank_bm25`** (fusion avec le dense) | Le texte juridique est riche en tokens exacts (n° d'articles, « Loi 65‑99 »). |
| Reranker (option) | `bge-reranker-v2-m3` | Gain de précision, à mesurer. |
| LLM local | **Ollama** + Qwen3 / Mistral 7‑8B | Inférence locale = souveraineté. |
| Framework RAG | **Aucun** (implémentation à la main) | Maîtrise et débogage de chaque étape. |
| Évaluation | Scripts + `pandas` | Contrôle total, métriques honnêtes. |

---

## 4. Plan d'action par phases

| Phase | Objet | Livrable de fin de phase |
|---|---|---|
| **S1** | Acquisition du corpus + extraction brute + découpage article | Liste d'articles brute, fidélité vérifiée. |
| **S2** | Structuration + découpage intelligent (métadonnées, hiérarchie) | Corpus structuré reproductible au format JSONL. |
| **S3** | Premier pipeline RAG bout‑en‑bout | CLI : question → réponse avec articles cités. |
| **S4** | Ancrage, citation, abstention | Réponses fiables + abstention hors périmètre. |
| **S5** | Qualité de recherche (BM25, reranking) + jeu de Q/R de référence | Recherche améliorée + jeu d'évaluation documenté. |
| **S6** | Exécution de l'évaluation + métriques | Rapport de performance + analyse d'erreurs. |
| **S7** | Durcissement, reproductibilité, marge | Prototype propre et reproductible. |
| **S8** | Rapport, soutenance, reproductibilité finale | Rapport + démo + dépôt reproductible. |

Un **journal de bord** (`JOURNAL.md`) est tenu quotidiennement : chaque décision, résultat et difficulté y est consigné, pour la traçabilité et le rapport final.

---

## 5. État d'avancement (au 7 juillet 2026)

**Mission 1 — fondation en bonne voie, en avance sur le calendrier.**

Réalisé :
- Extraction du texte du Code du travail (version française consolidée 2011) via PyMuPDF ; correction d'un problème d'encodage des accents (UTF‑8).
- Parser écrit **à la main** : découpage automatique du texte en articles via expression régulière ancrée en début de ligne (`re.split` + groupe capturant, mode multiligne).
- **588 articles** proprement séparés ; avant‑propos (dahir, préface) et table des matières isolés et traités à part.
- Structuration en liste d'objets `{"article_number", "article_text"}`, numéros normalisés (l'« Article premier » devient `"1"`), stockés en chaîne pour la cohérence des comparaisons et citations en aval.

Prochaines sous‑étapes (S2) :
- Nettoyage du texte (suppression des marqueurs de pagination, normalisation des retours à la ligne).
- Ajout des métadonnées de hiérarchie (`livre`, `titre`, `chapitre`, `section`).
- Sérialisation JSONL déterministe + vérification manuelle de fidélité sur un échantillon d'articles.

---

## 6. Analyse des sources : version française vs version arabe

Une comparaison a été menée entre les deux versions disponibles du Code du travail *(détail complet : `comparaison-code-du-travail-FR-AR.md`)*.

**Constats clés :**
- Les deux documents sont le **même Code** (Loi 65‑99, 589 articles, structure identique en Livres / Titres / Chapitres / Sections).
- **Version FR :** consolidée au **26 octobre 2011**.
- **Version AR :** consolidée au **9 février 2021** — donc plus récente. Elle intègre la **loi 02.21 (2021)**, qui modifie **uniquement les articles 32 et 256** (rétablissement du service militaire). Tout le reste est identique.
- En droit marocain, **le texte arabe fait juridiquement foi** ; le français est une traduction officielle du Bulletin officiel.

**Vérification technique des fichiers :**
- Le fichier arabe exploitable (144 pages, version 2021) contient une **couche texte** extractible.
- Une autre copie arabe reçue est un **PDF scanné** (images, aucune couche texte) → inexploitable sans OCR ; écartée.

**Décision retenue pour la fondation du RAG :**
1. **Corpus technique primaire = version française** (extraction propre, évaluable, quasi finalisée), avec `date_consolidation` en métadonnée.
2. **Alignement de l'état 2021** : correction ciblée des **articles 32 et 256** côté FR pour refléter la version en vigueur, plutôt que l'état abrogé de 2011.
3. **Reconnaissance explicite de la limite** dans le rapport : la version faisant foi est l'arabe ; le système s'appuie sur la traduction française alignée pour des raisons de faisabilité, avec le delta d'un seul texte modificateur documenté.
4. **Version arabe** conservée comme corpus de référence et piste d'expérimentation (Mission 4).

> **Point de vigilance identifié** : même la version arabe de 2021 n'est pas l'état le plus récent en 2026 (un projet de loi 032.26 modifiant l'article 193 est en cours de processus législatif). D'où la nécessité d'un champ de métadonnée `date_consolidation` par document et d'une note de fraîcheur — un assistant juridique doit dater ses sources.

### 6.1 Stratégie multilingue — couche de traduction (Mission 4)

Le cœur du système reste **entièrement français** (corpus, embeddings, recherche, génération, citations). Le support de l'arabe et de la darija est traité comme une **couche de traduction greffée aux extrémités**, sans toucher au moteur :

```
Question (AR / darija)
      │  traduction → FR
      ▼
Pipeline RAG français  (recherche → articles cités → génération)
      │  traduction → AR
      ▼
Réponse (AR) + numéros d'articles cités (inchangés, indépendants de la langue)
```

**Justification :** cette approche isole toute la difficulté de l'arabe (extraction RTL, qualité des embeddings arabes, évaluation d'une réponse juridique arabe) hors du pipeline principal. Le « raisonnement » reste dans la langue la mieux maîtrisée par le système, à l'image des assistants qui traitent en langue forte puis restituent dans la langue de l'utilisateur.

**Points de vigilance (à documenter comme limites) :**
- La **traduction de terminologie juridique** est délicate ; elle est toutefois plus tolérable à l'étape de *recherche* (il suffit de retrouver le bon article), et la **citation reste le numéro d'article**, indépendant de la langue et donc toujours vérifiable.
- Une réponse arabe passe par une traduction du français (lui‑même traduction de l'arabe faisant foi) → à assumer explicitement pour un usage **informatif**, jamais comme conseil juridique.
- **Variante à évaluer :** BGE‑M3 étant nativement multilingue, une requête arabe peut parfois retrouver directement l'article français pertinent (recherche translingue **sans** étape de traduction explicite). À comparer avec l'approche par traduction dans la Mission 4.

---

## 7. Décisions techniques structurantes

- **Unité de découpage = l'article.** C'est l'unité de citation naturelle du droit ; un article = une source citable.
- **Pas de framework RAG au départ.** Implémentation manuelle pour maîtriser et déboguer chaque étape ; refactorisation possible plus tard si justifiée.
- **Séparation recherche / génération au débogage.** La plupart des réponses erronées viennent d'une mauvaise *recherche*, pas de la génération ; les articles retrouvés sont toujours affichables avant l'appel au modèle.
- **Abstention par seuil avant appel au modèle.** Mécanisme indépendant du modèle, plus fiable que la seule consigne de refus dans le prompt.

---

## 8. Risques et mesures

| Risque | Mesure |
|---|---|
| Bruit d'extraction PDF propagé dans les réponses | Découpage structurel par article + nettoyage documenté ; vérification manuelle de fidélité. |
| Hallucination / sur‑affirmation du modèle local | Seuil d'abstention avant le modèle + prompt d'ancrage strict + vérification des citations + température basse. |
| Évaluation sans expertise juridique | Questions factuelles à réponse directe tirée du texte ; échantillon soumis à validation de l'encadrant ; caveats de taille d'échantillon. |
| Dérive de version du corpus (textes amendés) | Source officielle, `date_consolidation` en métadonnée, note de fraîcheur, patch des articles divergents. |
| Qualité arabe / darija (RTL, extraction) | Périmètre arabe traité en expérimentation ; version française comme corpus primaire. |

---

## 9. Livrables de fin de stage

- Corpus structuré, documenté et reproductible du Code du travail (JSONL, métadonnées).
- Pipeline RAG local (CLI) : question → réponse sourcée avec citation d'articles + abstention.
- Jeu de questions/réponses de référence et rapport d'évaluation (métriques + analyse d'erreurs).
- Rapport de stage + dépôt reproductible depuis un clone propre + démonstration.

---

*Document d'avancement — mis à jour au 7 juillet 2026.*
