# Sovereign Legal RAG Assistant

Assistant conversationnel (RAG) sur le **droit du travail marocain** (Loi n° 65‑99 — Code du travail).
Français d'abord, **citation obligatoire des articles sources**, **abstention explicite** hors périmètre,
et exécution **entièrement locale / open-source** — aucune donnée ni requête ne quitte la machine.

> Stage — Pulsaride Solutions · 8 semaines · démarré le 1ᵉʳ juillet 2026.

## Principe

```
Question en langage naturel
        │
        ▼
Recherche hybride (dense + lexicale, fusionnées par RRF)
        │
        ▼
Génération ancrée : réponse fondée UNIQUEMENT sur les articles retrouvés
        │
        ▼
Citation systématique des numéros d'articles + abstention si l'info n'y est pas
```

Le système relève de la **restitution d'information juridique**, pas du conseil juridique personnalisé —
toute réponse rappelle qu'elle est informative.

## Stack technique

| Couche | Choix |
|---|---|
| Extraction PDF | PyMuPDF |
| Embeddings | BGE‑M3 (multilingue, local) |
| Base vectorielle | Chroma (persistante, embarquée) |
| Recherche lexicale | BM25 (`rank_bm25`), fusion RRF avec le dense |
| LLM | Mistral 7B via Ollama (local) |
| Format du corpus | JSONL |

Aucun framework RAG (LangChain/LlamaIndex) : pipeline codé à la main pour rester compréhensible et
défendable ligne par ligne. Justification détaillée de chaque choix : [docs/Plan-Action-Projet.md](docs/Plan-Action-Projet.md) §4.

## Structure du dépôt

```
├── data/
│   ├── raw/                       # PDF sources (Code du travail FR + AR), non modifiés
│   ├── processed/
│   │   └── corpus_chunks.jsonl    # Corpus structuré, un article par ligne
│   └── chroma/                    # Base vectorielle (générée, non versionnée)
├── docs/                          # Plan de conception, analyses, arbitrages techniques
│   └── Plan-Action-Projet.md      # Document de conception technique complet
├── eval/
│   └── questions-test.md          # Jeu de test manuel (questions + réponses attendues)
├── src/
│   ├── parser.py                  # PDF → corpus JSONL (extraction, hiérarchie, nettoyage)
│   ├── database.py                # Corpus → index vectoriel Chroma (embeddings BGE-M3)
│   ├── retriever.py               # Recherche hybride (dense + BM25, fusion RRF)
│   └── generator.py               # Génération ancrée via Ollama (citations + abstention)
├── JOURNAL.md                     # Carnet de bord quotidien (décisions, bugs, résultats)
└── requirements.txt
```

## Installation

```bash
git clone <repo>
cd "Sovereign Legal RAG Assistant"
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell)
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

Le LLM local tourne via [Ollama](https://ollama.com/download) :

```bash
ollama pull mistral:7b
```

Optionnel mais recommandé — un compte Hugging Face évite les limites de débit au premier téléchargement
des poids BGE‑M3 (~2.2 Go, mis en cache ensuite) :

```bash
hf auth login
```

## Utilisation

Pipeline complet, dans l'ordre :

```bash
python src/parser.py       # PDF -> data/processed/corpus_chunks.jsonl (589 articles)
python src/database.py     # Corpus -> index vectoriel Chroma (BGE-M3)
python src/generator.py "Quelle est la durée du congé annuel payé ?"
```

`database.py` télécharge et met en cache le modèle d'embeddings au premier lancement (~2.2 Go,
one-time). `retriever.py` peut aussi être exécuté seul pour inspecter la recherche sans générer de
réponse :

```bash
python src/retriever.py "Quelle est la durée du congé annuel payé ?"
```

### Tester

[`eval/questions-test.md`](eval/questions-test.md) — 15 questions avec réponse attendue et article
source, vérifiées contre le texte réel du corpus, dont un test d'abstention volontaire (question hors
périmètre du Code du travail). Chaque question a sa commande prête à copier-coller.

## État d'avancement

| Phase | Contenu | Statut |
|---|---|---|
| S1‑S2 | Extraction, découpage par article, métadonnées de hiérarchie, corpus JSONL | ✅ |
| S3 | Pipeline RAG bout‑en‑bout : embeddings, recherche hybride, génération citée | ✅ |
| S4 | Vérification automatique des citations, seuil d'abstention pré‑LLM, CLI (`app.py`) | ⬜ |
| S5 | Reranking par cross‑encodeur, jeu de référence (30‑50 questions) | ⬜ |
| S6 | Évaluation (Recall@k, MRR) et analyse d'erreurs | ⬜ |
| S7 | Durcissement, reproductibilité | ⬜ |
| S8 | Rapport de stage, soutenance | ⬜ |

Journal détaillé : [JOURNAL.md](JOURNAL.md). Plan complet et justification des choix techniques :
[docs/Plan-Action-Projet.md](docs/Plan-Action-Projet.md).
