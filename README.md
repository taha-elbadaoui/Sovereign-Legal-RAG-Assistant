# Sovereign Legal RAG Assistant

Un assistant conversationnel (RAG) sur le **droit du travail marocain** (Loi n° 65‑99 — Code du travail).
Français d'abord, avec **citation obligatoire des articles sources** et **abstention explicite** hors périmètre.
Conçu pour tourner en **local / open‑source** (souveraineté des données).

> Stage — Pulsaride Solutions · 8 semaines · démarré le 1er juillet 2026.

## Principe

Question en langage naturel → **recherche** des articles pertinents → **génération** d'une réponse fondée
*uniquement* sur ces articles → **citation** des numéros d'articles → **abstention** si la réponse n'est pas dans le texte.

Le système relève de la **restitution d'information juridique**, pas du conseil juridique personnalisé.

## Structure du dépôt

```
├── data/
│   └── raw/          # PDF sources (Code du travail FR + AR)
├── docs/             # Plan d'action, analyses, arbitrages techniques
├── src/
│   └── parser.py     # Extraction PDF + découpage par article (Mission 1)
├── JOURNAL.md        # Carnet de bord quotidien (décisions, résultats, impasses)
└── requirements.txt  # Dépendances Python épinglées
```

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell)
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

## Exécution

```bash
python src/parser.py
```

Extrait le texte du Code du travail, le découpe en **588 articles** (`{"article_number", "article_text"}`),
et isole l'avant‑propos et la table des matières.

## État d'avancement

- ✅ **Mission 1 (en cours)** — extraction PDF + découpage par article. Voir [JOURNAL.md](JOURNAL.md).
- ⬜ Mission 2 — pipeline RAG (embeddings, base vectorielle, génération sourcée).
- ⬜ Mission 3 — évaluation (jeu de Q/R de référence, métriques, analyse d'erreurs).
- ⬜ Mission 4 (optionnelle) — support arabe / darija via couche de traduction.

Plan complet : [docs/Plan-Action-Projet.md](docs/Plan-Action-Projet.md).
