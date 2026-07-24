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
│   ├── questions-test.md          # Jeu de test manuel (questions + réponses attendues)
│   ├── reference_qa.jsonl         # Jeu de référence (37 questions, articles attendus)
│   └── run_eval.py                # Métriques de recherche (Recall@k, MRR)
├── src/
│   ├── parser.py                  # PDF → corpus JSONL (extraction, hiérarchie, nettoyage)
│   ├── database.py                # Corpus → index vectoriel Chroma (embeddings BGE-M3)
│   ├── retriever.py               # Recherche hybride (dense + BM25 + RRF), reranking optionnel
│   ├── generator.py               # Génération ancrée via Ollama (Mistral 7B)
│   └── app.py                     # Orchestrateur : abstention + citations + vérification (CLI)
├── web/
│   └── index.html                 # Interface web conversationnelle (chat, type Gemini/ChatGPT)
├── serve.py                       # Serveur web local (stdlib, réponses en streaming)
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

**Préparation** (une seule fois — construit le corpus puis l'index vectoriel) :

```bash
python src/parser.py       # PDF -> data/processed/corpus_chunks.jsonl (589 articles)
python src/database.py     # Corpus -> index vectoriel Chroma (télécharge BGE-M3, ~2.2 Go)
```

**Interface web conversationnelle** (recommandé — chat type Gemini/ChatGPT, réponses en streaming) :

```bash
python serve.py
```

Puis ouvrir **http://localhost:8000**. Aucune dépendance web à installer (serveur en stdlib).

**Ou en ligne de commande :**

```bash
python src/app.py "Un employeur peut-il licencier une salariée enceinte ?"
```

Les deux passent par le même moteur (`src/app.py`) : recherche → garde-fou d'abstention
→ génération citée → vérification que chaque article cité était bien dans le contexte.

Pour inspecter la seule recherche (sans génération) :

```bash
python src/retriever.py "Quelle est la durée du congé annuel payé ?"
```

### Évaluation

```bash
python eval/run_eval.py
```

Compare dense seul / BM25 seul / hybride sur le [jeu de référence](eval/reference_qa.jsonl)
(37 questions). Résultats mesurés (Recall@5 / MRR) :

| Méthode | Recall@5 | MRR |
|---|---|---|
| Dense seul | **0.969** | **0.891** |
| BM25 seul | 0.781 | 0.628 |
| Hybride (RRF) | 0.875 | 0.794 |

> Sur des questions en langage naturel, la recherche dense domine — les reformulations favorisent
> le sémantique. L'hybride aiderait davantage sur des requêtes à tokens exacts. Constat mesuré, pas
> supposé (cf. [JOURNAL.md](JOURNAL.md)).

## État d'avancement

| Phase | Contenu | Statut |
|---|---|---|
| S1‑S2 | Extraction, découpage par article, métadonnées de hiérarchie, corpus JSONL | ✅ |
| S3 | Pipeline RAG bout‑en‑bout : embeddings, recherche hybride, génération citée | ✅ |
| S4 | Abstention pré‑LLM, vérification des citations, orchestrateur CLI + interface web | ✅ |
| S5 | Reranking par cross‑encodeur (option), jeu de référence (37 questions) | ✅ |
| S6 | Évaluation (Recall@k, MRR) sur dense / BM25 / hybride | ✅ |
| S7 | Durcissement, reproductibilité | 🔶 en cours |
| S8 | Rapport de stage, soutenance | ⬜ |
| — | Extension multi‑codes + multilingue (FR/EN/AR) | ⬜ à venir |

Journal détaillé : [JOURNAL.md](JOURNAL.md). Plan complet et justification des choix techniques :
[docs/Plan-Action-Projet.md](docs/Plan-Action-Projet.md).
