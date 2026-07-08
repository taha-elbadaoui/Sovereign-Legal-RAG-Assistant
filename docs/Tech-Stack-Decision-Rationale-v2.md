# Tech Stack — Decision Rationale
*For the internship report's "decisions + rationale" section and defense Q&A prep.*

---

## The two filters behind every choice

Almost every decision below falls out of two constraints. State these in your defense and the rest follows:

1. **Sovereignty → must run local / open-source.** This alone eliminates every API option: OpenAI/Cohere embeddings, Cohere rerank, GPT-4/Claude/Gemini generation, and RAGAS with a cloud judge. Many "why not X" answers are simply *"X is an API; the citizen's query can't leave the country."*
2. **Beginner + small corpus (~thousands of chunks) + 8 weeks → optimize for understandability and developer experience, not production scale.** At this corpus size **every vector store is instant**, so raw performance is never the deciding factor. This filter explains Chroma over Milvus, hand-rolling over a framework, and Ollama over vLLM.

---

## Per-technology decisions

| Decision | I chose | Over | The deciding factor (defensible "why") | Honest caveat / when I'd switch |
|---|---|---|---|---|
| **Language** | Python 3.11 | JS/Node, Rust | The entire ML/NLP/RAG ecosystem — models, libraries, tutorials, local-inference tooling — is Python-first. Not a real debate. | None worth defending. |
| **PDF/text extraction** | PyMuPDF (`fitz`) + pdfplumber backup | pypdf, pdfminer, `unstructured` | PyMuPDF is fast with reliable accent/Unicode fidelity; pdfplumber handles messy layouts/tables. Both give me **raw control over how the law is cut** — auto-parsers like `unstructured` hide that. | If the source is HTML, skip all of this and use BeautifulSoup. Best case: avoid PDF entirely. |
| **Embeddings** | BGE-M3 (`BAAI/bge-m3`) | OpenAI/Cohere embeddings; multilingual-e5; MiniLM | **Sovereignty rules out API embeddings.** Among local models, BGE-M3 gives the best mix of French+Arabic coverage, long context (8192 tokens → no article truncation), and retrieval quality. | `multilingual-e5-base` is a legitimate lighter/simpler alternative (needs `query:`/`passage:` prefixes); newer families (e.g. Qwen3-Embedding) have since appeared — I checked the current MTEB multilingual leaderboard and kept BGE-M3 as a well-documented, defensible baseline. Genuinely a reasonable-people-differ call; e5 if hardware is tight. |
| **Vector DB** | Chroma (persistent) | FAISS, Qdrant, Milvus/Weaviate, pgvector | At ~thousands of chunks **performance is irrelevant**, so I optimized DX. Chroma is embedded (no server), persists to disk, and does metadata filtering with a trivial API. | FAISS is a lower-level *library* — I'd hand-build metadata + persistence. Server DBs (Qdrant/Milvus) add ops overhead I don't need. **pgvector is a fair pick given my SQL background** — I traded SQL familiarity for zero ops. |
| **Lexical / hybrid retrieval** | BM25 (`rank_bm25`) + reciprocal rank fusion alongside dense retrieval | Dense-only retrieval | Legal queries are dense with **exact tokens** — article numbers, "Loi 65-99", fixed legal vocabulary — precisely where lexical matching beats embeddings. ~20 lines of code, fully local, and it produces a measured **dense vs BM25 vs hybrid** comparison, which is the kind of rigor the offer rewards. | If hybrid doesn't move recall@k on the eval set, drop it and report the numbers — a measured "no" is still a finding. Tuning the fusion adds one more knob. |
| **Reranker (optional)** | `bge-reranker-v2-m3` | Cohere Rerank; other cross-encoders | A cross-encoder reads the (query, passage) pair jointly → more precise than bi-encoder retrieval alone. Retrieve top-10, rerank to top-3 → cleaner context → better answers, fewer distractor chunks. Same family as BGE-M3, multilingual, **local**. | Optional: adds latency + a second model. Cohere Rerank is an API (sovereignty: no). Measure whether it actually beats plain dense retrieval before committing. |
| **Local LLM runtime** | Ollama | llama.cpp directly, vLLM, LM Studio, raw transformers | One command pulls + runs a quantized model and exposes a clean API — **minimal friction for a beginner**. | llama.cpp (which Ollama wraps) and raw transformers give more control but more setup. vLLM is built for high-concurrency serving I don't need for a single user. |
| **Local LLM model** | Qwen3 8B (or Mistral 7B) | GPT-4/Claude APIs; Llama 3.x 8B; 70B; ≤4B; Jais | **Sovereignty rules out frontier APIs.** The 7–8B class is the size that's good enough at instruction-following while still running on student hardware (70B is out of reach; ≤4B is weaker at the faithfulness this project lives on). Qwen3 for Arabic/multilingual coverage (it superseded Qwen2.5); Mistral for native French strength. **Verified the current model generation before committing** (small local models move fast). | Llama 3.x 8B is an equally fair pick. Choose by language priority: Mistral = French-only, Qwen = Arabic in play. Drop to Qwen3 4B only if hardware forces it. Jais (Arabic-specialist) is heavy and weak in French — not worth it for French-first. |
| **RAG framework** | None for the core (hand-roll); LlamaIndex *optional* later | LangChain or LlamaIndex from the start | For **one bounded corpus** the RAG loop is ~150 lines. Hand-rolling = I understand every step, debugging is direct, no API churn — and in a defense, explaining my own pipeline beats "the framework does it." | The most debatable call. A framework earns its place if the project grows (many sources, agents, routing). **If the supervisor wants LangChain/LlamaIndex as a CV/learning outcome, that changes the decision — ask him.** |
| **Evaluation** | Custom scripts + `pandas` + manual grading | RAGAS as the main evaluator | On a 30–50 question set I'd rather **read every answer** than trust an LLM judge — manual grading is more honest and surfaces the failure modes I need for the limits analysis. Retrieval metrics (recall@k, MRR) I automate because gold article IDs make them objective. | RAGAS is automatable but its default judge needs a strong (often non-local, paid) model → fights sovereignty and trust. Fine as an optional *secondary* signal, not the spine. |
| **Corpus file format** | JSONL | CSV, Parquet, a database | One chunk per line: human-readable, handles nested metadata cleanly, **Git-diffable**, streams line-by-line. Ideal for a few-thousand-record text corpus and the offer's reproducibility requirement. | CSV chokes on text with commas/newlines + nested metadata. Parquet is binary (not Git-diffable) — overkill. A DB is unnecessary indirection for a static, version-controlled corpus. |
| **UI (optional)** | Streamlit or Gradio | React/Flask web app | Turns a Python function into a web demo in minutes with near-zero web code — perfect for the defense. The deliverable is the RAG system, not a product UI. | A real frontend is more work and not the point. CLI alone is an acceptable deliverable; this is a nice-to-have. |

---

## The genuinely debatable calls (be honest about these in the defense)

These aren't "right vs wrong" — a juror who knows the space will respect *"here's why I chose X, and here's the legitimate case for Y."*

- **BGE-M3 vs multilingual-e5** — close call; e5 is lighter and simpler. BGE-M3 edges it on multilingual breadth + long context.
- **Chroma vs pgvector** — pgvector plays to my SQL strength and would work fine; I chose Chroma for zero ops.
- **Qwen2.5 vs Mistral vs Llama 3.1 8B** — all defensible; the tiebreaker is which language matters most.
- **No framework vs LlamaIndex** — tied to scope and to whether framework experience is itself a goal of the internship.
- **Dense-only vs hybrid (BM25 + dense)** — hybrid is cheap and legal text favors exact-token matching, so the default is to add it; but the honest position is *"I measured it, here's the delta"* — and if the delta is ~0 on this corpus, dropping it is the right call.

---

## Corpus authority note (belongs in the limits section, not the stack table)

The legally authoritative version of Moroccan law is the **Arabic** text; the French Bulletin Officiel is an official *translation*. This system grounds its answers in the French corpus — a deliberate, documented scope choice consistent with the offer's own principle that the law keeps its authority in its original language. State it openly: cite the BO edition and version date, and note that for legal authority the Arabic original prevails.

---

## One-line summary for the report

> The stack is the intersection of two hard constraints: **sovereignty** (everything must run local/open, which eliminates all API-based components) and **a bounded beginner project** (favor understandability and developer experience over production-scale performance, since the corpus is small enough that scale is a non-issue).


## Foundations (the mental model)

retrieval augmented generation explained — what RAG is, end to end
RAG vs fine-tuning — why we retrieve the law instead of training it into the model
text embeddings explained — what an embedding actually is
cosine similarity explained — why angle = semantic closeness
vector database explained — what the store does under the hood

Mission 1 — corpus & chunking

chunking strategies for RAG — fixed vs recursive vs semantic vs structural
chunk size RAG retrieval quality — why too-big and too-small both hurt

Mission 2a — embeddings, vector store, reranking

best embedding model for RAG 2025 — where BGE-M3 sits vs the field
multilingual embedding models comparison — the FR/AR angle
open source vs OpenAI embeddings — why local, not an embedding API
Chroma vs FAISS — the vector-DB choice
bi-encoder vs cross-encoder — why retrieve-then-rerank, not retrieve alone
reranker RAG explained — what the reranker adds

Frameworks (the contrarian call I made)

LangChain vs LlamaIndex 2025 — what each is for
RAG without LangChain — the argument for hand-rolling first (watch this one; it's the case behind my advice)

Local model

Ollama tutorial — running a model locally
best local LLM for RAG 2025 — Qwen vs Mistral vs others
local LLM vs API tradeoffs — why local, and what it costs you in quality
LLM quantization GGUF explained — why Q4, what you lose

Mission 2b — grounding, citation, abstention

reduce hallucination in RAG — grounded generation
LLM grounding faithfulness — keeping answers tied to the source

Mission 3 — evaluation

how to evaluate RAG — the metrics landscape
recall@k MRR information retrieval — the retrieval metrics
RAGAS tutorial — the automated-eval library (+ its limits)
LLM as a judge problems — why I told you to grade manually on a small set

Stretch — multilingual

multilingual RAG cross-lingual retrieval — the pivot idea