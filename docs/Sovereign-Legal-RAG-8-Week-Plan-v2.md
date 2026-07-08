# Sovereign Legal RAG Assistant — 8-Week Execution Plan
**Internship:** Pulsaride Solutions · 1 Jul – 31 Aug 2026 · full remote · **Week 0 completed ✅**
**Project:** RAG assistant over Moroccan law (starting: Code du travail / Loi 65-99), French-first, mandatory source citation, explicit abstention, local/open-source where possible.

> ⚠️ **Duration mismatch — handle in Week 1, not Week 8.** The offer PDF says *4 mois*; the agreed duration is **8 weeks**. State this explicitly in your first written check-in to M. Salihi ("scope confirmed for 8 weeks: Missions 1–3 committed, Mission 4 as a documented experiment if time allows") so his expectations are calibrated to the offer's own bounded-scope philosophy, not to a 4-month timeline.

---

## How to use this plan (read once)

Two rules govern everything below:

1. **The foundation caps the ceiling.** Mission 1 (corpus + chunking) determines the maximum quality of Missions 2–3. Sloppy chunks → no retrieval trick can recover. Resist the urge to rush to the "AI" part.
2. **Keep a lab notebook from Day 1.** A single `JOURNAL.md` in the repo: every decision (and *why*), every result, every dead end. Update it daily, even one line. Week 8 (report + defense) becomes copy-paste instead of archaeology. The offer says honest limits analysis counts **as much as** performance — your notebook is where that analysis is born.

A useful instinct throughout: **separate retrieval from generation when debugging.** Most "the answer is wrong" bugs are actually "the right chunk wasn't retrieved." Always be able to print the retrieved chunks *before* the LLM touches them.

---

## Honest assessment — achievable vs. stretch

**Genuinely achievable in 8 weeks at your level (full-time):**
- A clean, reproducible, article-level corpus of the Code du travail with rich metadata.
- A working French RAG pipeline: question → retrieved articles → sourced answer, running on a local model.
- Reliable citation (article numbers) + abstention on clearly out-of-scope questions.
- A real evaluation: 30–50 reference Q&A, retrieval recall@k, manual correctness/citation grading, abstention metrics, and an honest error analysis.
- A clean report + defense + a repo that rebuilds from scratch.

**Should stay a stretch (be willing to drop entirely):**
- Multilingual / darija pivot. Arabic is hard; **darija is a research problem**, not a feature. Treat it as a small documented *experiment* at the very end, if and only if the core is solid.
- A polished web UI. A CLI is a perfectly respectable deliverable. A minimal Streamlit demo is a *nice-to-have* for the defense, not a goal.

**The single biggest non-technical risk:** under-communicating as a remote first-year. Share this plan with M. Salihi in Week 0, demo your thin end-to-end slice in Week 3 (early, ugly, working), and do a weekly written check-in. Visible progress on a narrow scope beats silent ambition.

---

## Minimal recommended tech stack (one coherent beginner set)

| Layer | Pick | Why | Lighter alternative |
|---|---|---|---|
| Language / env | Python 3.11 + `venv` | Stable, well-supported | conda |
| PDF / text extraction | **PyMuPDF (`fitz`)** + `pdfplumber` as backup | Fast, good with French accents | `pdfminer.six` |
| Embeddings | **BGE-M3** (`BAAI/bge-m3`) via `sentence-transformers` | Multilingual (FR + AR), long context, strong retrieval, runs local | `intfloat/multilingual-e5-base` (smaller, needs `query:`/`passage:` prefixes) |
| Vector DB | **Chroma** (persistent) | Easiest DX, metadata filtering, persistence for free | FAISS (faster at scale, lower-level) |
| Lexical / hybrid retrieval | **`rank_bm25`** alongside dense (merge via reciprocal rank fusion) | Legal queries are full of exact tokens (article numbers, "Loi 65-99", fixed legal terms) where lexical beats embeddings; ~20 lines of code, and "dense vs BM25 vs hybrid, measured" is a strong report section | dense-only (but then say why) |
| Reranker (optional) | `BAAI/bge-reranker-v2-m3` | Multilingual cross-encoder, lifts precision | skip it |
| Local LLM runtime | **Ollama** | One-command local inference, handles quantization | llama.cpp directly |
| Local LLM model | **Qwen3 8B** (better Arabic/multilingual; superseded Qwen2.5) or **Mistral 7B** (strong French) | Good size/quality, open | Qwen3 4B if hardware-limited |
| RAG framework | **None for the core** (hand-roll); LlamaIndex *optional* later | You'll actually understand and can debug it | LlamaIndex from the start |
| Evaluation | custom scripts + `pandas` | Full control, honest, small set | RAGAS (LLM-judge; note sovereignty/cost caveat) |
| UI (optional) | Streamlit or Gradio | Fast demo for defense | CLI only |
| Repo | Git + GitHub + `JOURNAL.md` | Versioning + your analysis spine | — |

> ⚠️ **Verify latest model versions before committing (Week 1 task).** Check the current MTEB *multilingual* leaderboard for embeddings (BGE-M3 remains a defensible baseline, but newer contenders like the Qwen3-Embedding family exist) and the Ollama library for the current small-LLM generation. If Week 0 already pulled `qwen2.5:7b`, it works — upgrading to `qwen3:8b` is a one-command swap behind your model interface. Whatever you choose, **log the verification and the reason in `JOURNAL.md`**: "I checked and chose deliberately" beats "I copied a plan." The *methodology* below doesn't change regardless.

**Hardware reality check (do this in Week 0):** A 7B model at Q4 quantization needs ~5 GB.
- NVIDIA GPU (≥6 GB VRAM): fast, ideal.
- Apple Silicon (M-series, ≥16 GB RAM): works well via Metal.
- CPU-only: works but slow (a few to low-tens of tokens/sec). Usable for a demo, painful for fast iteration → use **Qwen3 4B** and lower your expectations on speed, not on correctness.

---

## Week 0 — Prep (the few days before 1 July) ✅ DONE

**Goal:** arrive warm. Don't write pipeline code; de-risk setup and build a mental model. *Setup is where beginners lose 3 days.*

**Learn / absorb (a few hours, not days):**
- What an **embedding** is: a vector that represents *meaning*, so that semantically similar texts land close together.
- **Cosine similarity**: why the *angle* between vectors measures semantic closeness (not magnitude).
- The **RAG loop** in one sentence: *retrieve relevant text, then ask the model to answer using only that text.*
- Watch one solid RAG explainer end-to-end (concept, not a framework tutorial). Read the Pulsaride offer twice — especially the maternity-leave example; that's your north-star interaction.

**Set up:**
- Install Python 3.11, create a `venv`, set up the GitHub repo (`README`, `JOURNAL.md`, `requirements.txt`, `src/`, `data/`, `eval/`).
- Install **Ollama**; run `ollama pull qwen2.5:7b` (or `mistral`); confirm you can chat with it from the terminal. **This is your hardware test.**
- `pip install sentence-transformers chromadb pymupdf pdfplumber pandas`. Embed two toy sentences with BGE-M3, print their cosine similarity. That's your "hello world."
- Locate the **Code du travail (French)** from an official/authoritative source (e.g. SGG Maroc). Note the *date/version* — legal texts get amended.

**Decision:** Qwen 7–8B class vs Mistral 7B → **default Qwen (now Qwen3 8B)** if you'll touch Arabic at all; **Mistral** if you're committing to French-only. If you already pulled `qwen2.5:7b` in Week 0, swap to `qwen3:8b` when convenient — one command, same interface.

**Checkpoint:** Ollama answers a question locally; BGE-M3 produces embeddings; repo scaffolded; corpus source identified.

**Likely blocker:** Ollama/GPU driver issues, or model download stalls. *Unstuck:* start with a 3B model to confirm the path works, then pull 7B. On CPU-only, accept slowness now and decide on the smaller model.

---

## Week 1 — Foundations + corpus acquisition (Mission 1, part 1)

**Learning phase:**
- `sentence-transformers` basics: `model.encode(...)`, batching, what comes back.
- Tokenization at a high level (why text becomes tokens; why context length is finite).
- What a **vector store** does conceptually (stores vectors + lets you find nearest neighbors).
- The structure of a legal code: **Livre → Titre → Chapitre → Section → Article**. The **article is your natural unit.**

**Concrete tasks (ordered):**
1. Acquire the Code du travail. Strongly prefer a clean **HTML/structured** source over PDF if one exists — it saves days.
2. Extract raw text (PyMuPDF first; pdfplumber if layout is messy). Inspect it manually — look for headers/footers, page-break artifacts, accent corruption (é, è, ç).
3. First-pass parse: detect "Article N" boundaries with a regex and split into article-level text. Don't perfect it yet — get a rough article list.
4. Eyeball 10 random extracted articles against the source for fidelity. Log issues in `JOURNAL.md`.

**Tools & why:** PyMuPDF (fast, accent-safe), pdfplumber (better on awkward layouts), plain regex for article detection (the structure is regular — no ML needed here).

**Technical decisions:**
- **Source format** → **default: cleanest structured source available**; PDF only if forced. Reasoning: PDF parsing noise propagates into every downstream answer.
- **Encoding** → ensure UTF-8 throughout; verify French accents survive the round trip.

**Checkpoint / deliverable:** raw corpus acquired + a rough article-level split (list of articles with numbers and text), fidelity spot-checked.

**Likely blockers:** PDFs split articles across pages; footers inject junk mid-article; accents mangle. *Unstuck:* try the other extractor; strip repeated header/footer lines by frequency; if one source is hopeless, find another. **Time-box PDF wrestling to ~1.5 days** — switching sources beats fighting a bad PDF.

---

## Week 2 — Corpus structuring + intelligent chunking (Mission 1 core)

This is the deliverable that secretly determines your grade. Spend the week.

**Learning phase:**
- **Chunking strategies:** fixed-size, recursive, structural, semantic. Why **structural (by article)** is right here.
- Why **chunk size matters:** too big → retrieval gets diluted and you blow context limits; too small → you lose the context needed to answer.
- The role of **metadata** and **overlap**.

**Concrete tasks:**
1. Build a *robust, reproducible* parser: split into **one chunk per article**, attach metadata: `article_number`, `livre`, `titre`, `chapitre`, `section`, `heading`, `source`, `version_date`.
2. Handle **long articles**: sub-split into overlapping windows (~400–600 tokens, ~50–80 overlap) but keep the same `article_number` so citation stays clean.
3. **Prepend a context header to each chunk's text**, e.g. `"Code du travail > Livre II > ... > Article 152: <body>"`. This improves embedding quality *and* citability.
4. Serialize to **JSONL** (one chunk per line: `id`, `text`, `metadata`). Write it so re-running the script reproduces the file deterministically.
5. Document the pipeline in the README; log every edge-case decision.

**Tools & why:** pure Python + regex + `json`. No framework — you want full control over how the law is cut, because this is where errors are most expensive.

**Technical decisions:**
- **Chunk granularity** → **default: article = unit; sub-split only long articles** (keep article ID). Reasoning: matches how law is cited; one chunk = one citable source.
- **Context header in chunk text** → **default: yes.** Reasoning: a bare article body embeds worse and is harder to cite than one carrying its hierarchy.

**Checkpoint / deliverable:** **Mission 1 done** — a structured, documented, reproducible corpus (hundreds to ~2000 chunks) with metadata. This is a real, defensible deliverable on its own.

**Likely blockers:** sub-articles (152-1), embedded lists/tables, amended articles, articles with weird boundaries. *Unstuck:* handle the *common* case cleanly, **log and flag** the oddballs rather than over-engineering, and document the limitations openly (that documentation is itself a deliverable).

---

## Week 3 — First end-to-end RAG, hand-rolled (Mission 2 start)

**The most important week.** Goal: a thin vertical slice that works end-to-end. Ugly is fine.

**Learning phase:**
- Generating embeddings for a whole corpus with BGE-M3.
- Chroma API: create a persistent collection, add documents+metadata, query top-k.
- **Top-k retrieval** and what k controls.
- The **prompt-stuffing** pattern.
- Calling Ollama from Python (the `ollama` client).

**Concrete tasks:**
1. Embed all chunks; load into a **persistent Chroma collection** (store text + metadata).
2. Write `retrieve(question, k)`: embed query → Chroma top-k → return chunks + metadata.
3. Write `generate(question, chunks)`: build a prompt that includes the chunks and instructs the model to answer **only** from them and **cite the article number**; call Ollama (temperature low, e.g. 0.1).
4. Wire `ask(question)` = retrieve → generate. Build a tiny CLI.
5. Test on 5 questions (incl. the maternity-leave one). **Print the retrieved chunks** every time.

**Tools & why:** BGE-M3 (multilingual, strong), Chroma (persistence + metadata, zero ops), Ollama + Qwen3/Mistral (local = sovereign), **no framework** (you'll understand and debug the whole loop — ~150–200 lines).

**Technical decisions:**
- **Framework: LangChain vs LlamaIndex vs none** → **default: none now.** Hand-roll it. Reasoning: for one bounded corpus, frameworks add abstraction that obscures bugs you can't yet recognize. Refactor to LlamaIndex *later* only if it earns its place.
- **Vector DB: Chroma vs FAISS** → **default: Chroma.** Your corpus is tiny; FAISS's speed is irrelevant, and Chroma gives metadata + persistence free.
- **k** → **default: start k=4.** Tune later.

**Checkpoint / deliverable:** a local CLI where a typed question returns an answer **with cited articles**, end-to-end. It won't be reliable yet — that's Week 4. The *loop* working is the win.

**Likely blockers:** slow local inference; model ignores the context or won't cite; embedding model download size. *Unstuck:* drop to a smaller model if needed; iterate the prompt; **verify retrieval quality independently** (if the right article isn't in the printed top-k, fix retrieval before blaming generation).

---

## Week 4 — Grounding, citation, abstention (Mission 2 core — the hard part)

This is where "fiabilité" is won or lost, and where a local 7B model fights you.

**Learning phase:**
- Prompt engineering for **grounded** generation (answer strictly from context).
- Why small local models **over-claim and confabulate**.
- **Abstention strategies:** (a) a cheap **similarity-threshold gate** *before* calling the LLM, (b) prompt-level refusal.
- **Citation verification** (check the cited article actually appears in retrieved context).

**Concrete tasks:**
1. Harden the prompt: strict "use only the provided articles; cite the article number; if the answer isn't in them, say you don't have the information." Add 1–2 few-shot examples (one normal, one abstention).
2. Add a **threshold abstention gate**: if the best retrieval score is below a calibrated threshold, abstain **without** calling the LLM. (Cheap, reliable, model-independent.)
3. Add a **citation check**: after generation, confirm cited article numbers exist in the retrieved chunks; flag if not.
4. Handle the **multi-article answer** case (some answers span 2+ articles).
5. **Append the standard disclaimer footer to every generated answer** — *"Réponse fournie à titre informatif ; pour une situation particulière, consultez un professionnel."* — exactly as in the offer's north-star example. Two lines of code, and it operationalizes the offer's "no personalized legal advice" boundary.
6. Test on a handful of in-scope **and** deliberately out-of-scope questions; tune k and threshold.

**Tools & why:** same stack; the work is prompt + light Python logic, not new libraries.

**Technical decisions:**
- **Abstention threshold** → **default: calibrate empirically** against your embedding model's score distribution (look at scores for known-answerable vs. unanswerable questions; pick the separating value). There's no universal number.
- **Citation post-verification** → **default: yes** (lightweight, big trust payoff).

**Checkpoint / deliverable:** the engine now **reliably cites sources** and **abstains on clearly out-of-scope** questions (at least obvious cases). **Mission 2 substantially done.**

**Likely blockers:** the local model *won't* reliably say "I don't know" — it'll invent. *Unstuck:* lean harder on the **pre-LLM threshold gate** (it doesn't depend on the model's good behavior), constrain output format, keep temperature low, add few-shot abstention examples. Then **document that abstention reliability is model-limited** — that's an honest, valuable finding, not a failure.

---

## Week 5 — Retrieval quality + reranking + build the reference Q&A set (Missions 2→3 bridge)

**Learning phase:**
- Retrieval failure modes; **recall@k vs precision**; **MRR**.
- **Reranking** with a cross-encoder (retrieve many, rerank to a precise few).
- How to build a **gold/reference Q&A set**.

**Concrete tasks:**
1. **Add BM25 lexical retrieval** (`rank_bm25`) next to dense retrieval, merged with **reciprocal rank fusion**. Measure **dense vs BM25 vs hybrid** on your eval set — legal text is citation-heavy ("article 152", "Loi 65-99") and lexical matching often wins exactly there. Keep the comparison table; it's a report highlight either way.
2. Add `bge-reranker-v2-m3`: retrieve top-k (e.g. 10) → rerank → keep top-n (e.g. 3–4). **Measure whether it actually helps** (keep the before/after numbers — great for the report).
3. In parallel, build the **reference Q&A set**: 30–50 questions, each with the known answer **and** the supporting `article_number`. Include **~10 out-of-scope** questions to test abstention.
4. **Derive every gold answer directly from the article text** (lookup-style: "how many weeks of maternity leave?"). Record the exact article + answer span for each.
5. **Add paraphrase pairs for ~10 questions:** one "legal" phrasing and one colloquial citizen phrasing (e.g. *"durée du congé de maternité ?"* vs *"je suis enceinte, je peux m'absenter combien de temps ?"*), both mapped to the same gold article. The offer's entire premise is that citizens don't speak legal French — this is the direct test of the **vocabulary gap**, and a retrieval collapse on colloquial phrasing would be a headline finding.

**Tools & why:** bge-reranker (multilingual precision boost); `pandas`/JSONL for the eval set.

**Technical decisions:**
- **Reranker: add or skip** → **default: add it and measure.** A *measured* comparison is exactly the rigor the offer rewards; if it doesn't help, that's still a finding.
- **Eval set composition** → **default: lookup-style factual questions only**, plus out-of-scope items. Reasoning (critical): this keeps ground truth unambiguous *and* honestly scopes the project to "information retrieval & restitution," which the offer explicitly states it is — **not legal interpretation.**

**Checkpoint / deliverable:** improved retrieval + a **documented reference Q&A set** (the backbone of Mission 3).

**Likely blockers:** building the set is tedious and you'll be tempted to write interpretive/ambiguous questions. *Unstuck:* keep questions strictly factual; for each, store the exact article and answer span; **ask M. Salihi to sanity-check a sample**. This sidesteps your lack of legal expertise *by construction*.

---

## Week 6 — Evaluation execution + metrics (Mission 3 core)

**Learning phase:**
- The metrics: **retrieval recall@k & MRR** (automatable — you have gold article IDs), **answer correctness** (manual grade), **citation correctness**, **abstention precision/recall**.
- **LLM-as-judge** caveats (and why manual is more honest on a small set).
- RAGAS (optional, and its sovereignty/cost caveat).

**Concrete tasks:**
1. **Automate retrieval recall@k / MRR** (did the gold article appear in top-k?).
2. **Manually grade** answer correctness + citation correctness across the set (it's small enough — use a clear rubric: correct / partial / incorrect).
3. Compute **abstention metrics** on the out-of-scope questions.
4. **Split retrieval metrics by phrasing style** (legal vs colloquial paraphrase pairs from Week 5) and by retrieval mode (dense / BM25 / hybrid / +rerank) — this cross-table is the analytical core of the report.
5. Tabulate everything; do an **error analysis**: categorize each failure as *retrieval miss* vs *generation error* vs *bad abstention*.
6. (Optional) Try RAGAS for an automated faithfulness signal — **but note** its judge typically needs a strong (often non-local) model, which conflicts with sovereignty and costs money.

**Tools & why:** custom scripts + `pandas`; RAGAS optional and clearly caveated.

**Technical decisions:**
- **Manual grading vs LLM-judge** → **default: manual as the spine**, LLM-judge optional secondary. Reasoning: for 30–50 items, manual grading is more trustworthy and far more honest than an automated judge you can't fully trust.

**Checkpoint / deliverable:** **Mission 3 done** — a performance report with real numbers + an honest error analysis broken down by failure type. Per the offer, this analysis matters **as much as** raw performance.

**Likely blockers:** grading subjectivity; **small-sample noise** (30–50 questions = wide confidence intervals); no legal expertise for nuance. *Unstuck:* fix the rubric up front; keep questions unambiguous; **explicitly report sample size and its caveats** — overclaiming on a tiny sample is the rookie tell graders notice.

---

## Week 7 — Hardening, polish, buffer (+ optional multilingual probe)

Deliberately a **buffer week** — things *will* have slipped. Plan for it.

**Concrete tasks:**
1. Fix the biggest issues surfaced by Week 6's error analysis (prompt, threshold, chunking tweaks).
2. **Reproducibility pass:** README, pinned `requirements.txt`, one-command corpus rebuild, clear run instructions.
3. Clean the code; (optional) wrap a **minimal Streamlit/Gradio** demo for the defense.
4. **Only if the core is genuinely solid:** a *small* multilingual probe — e.g. test BGE-M3's cross-lingual retrieval by asking a French question, or a tiny experiment translating an Arabic/darija query to French for retrieval while keeping the French article as the authoritative source. **Document it as an experiment, not a feature.**

**Technical decisions:**
- **Invest in: robustness vs UI vs stretch** → **default order: reproducibility → robustness → minimal demo UI → multilingual (only if time).**

**Checkpoint / deliverable:** a polished, reproducible prototype + (optionally) a short multilingual experiment writeup.

**Likely blocker:** scope creep — the urge to add features instead of solidifying. *Unstuck:* **freeze features.** Make what exists solid and demo-able. A working narrow system beats a fragile broad one (your own stated preference).

---

## Week 8 — Report, defense, reproducibility (deliverables)

**Concrete tasks:**
1. Write the **internship report**: context → approach → architecture → **decisions + rationale** → results → **honest limits** → future work. (Your `JOURNAL.md` is 70% of this already.)
2. Build the **defense slides**: problem, sovereignty angle, architecture diagram, the maternity-leave demo, results table, limits, what you'd do next.
3. **Final reproducibility check:** clone fresh → rebuild corpus → run → demo. If it doesn't work from a clean clone, it doesn't work.
4. Prepare a **live demo** *and record a backup video* (hardware/inference can misbehave live).

**Checkpoint / deliverable:** final report + slides + reproducible repo + working demo. **Done.**

**Likely blocker:** underestimating writing time; live demo failing. *Unstuck:* you started the report in Week 1 via the journal; the backup video saves the defense.

---

## Key project-specific risks & mitigations

| Risk | Why it bites | Mitigation |
|---|---|---|
| **Arabic / RTL / darija handling** | Embedding & LLM quality drop sharply for Arabic; **darija is research-grade**; official text may only exist in Arabic for some codes | Keep multilingual a **stretch experiment**. If attempted, use BGE-M3's cross-lingual retrieval. **Scope darija out** of committed deliverables. |
| **Legal-text chunking difficulty** | Sub-articles, lists, tables, amendments break naive parsers | Exploit the article structure (it's an *advantage*): chunk by article + metadata, sub-split long articles keeping the ID, **document edge cases** instead of over-engineering. |
| **Hallucination / grounding control** | Local 7B over-claims and won't reliably abstain | **Threshold gate before the LLM** + strict grounded prompt + **citation verification** + low temperature. Document residual unreliability as a finding. |
| **Evaluation without legal expertise** | You're not a lawyer; nuanced answers are unjudgeable | **Lookup-style questions with gold answers taken directly from article text**; exclude interpretive questions; supervisor sanity-checks a sample; report small-sample caveats. |
| **Hardware for local inference** | No GPU → slow iteration | Start with Qwen3 **4B** if constrained; keep the LLM behind a **swappable interface**; accept slow-but-correct for the demo. |
| **Sovereignty vs. quality tension** | Local model is weaker than a frontier API | Name it openly. Local-first for the product; the quality gap **raises the stakes on grounding** and is **itself a finding to analyze** in the report. (Dev-time *test* questions ≠ production citizen data — a defensible nuance if you ever benchmark against a stronger model.) |
| **Corpus accuracy / version drift** | Legal texts get amended | Use an **official source**, record the **version date**, cite it, and note in limits that the system reflects a snapshot. |
| **French text is legally a translation** | The authoritative version of Moroccan law is the **Arabic** text; the French Bulletin Officiel is an official *translation*. Your system grounds answers in the French corpus. | Name it openly in the **limits section**: cite the BO édition de traduction officielle + version date, and note that for legal authority the Arabic original prevails. This mirrors the offer's own principle ("le texte de loi conserve sa valeur dans sa langue d'origine") — a juror with legal awareness *will* ask this. |
| **Remote + first-year communication** | Silent progress reads as no progress | Share this plan Week 0; **demo the Week-3 slice early**; weekly written check-ins with M. Salihi. |

---

## Closing principles

- **Narrow and solid beats broad and shaky.** You already know this — let it govern every scope decision.
- **Retrieval first, generation second** when debugging.
- **The cheap, model-independent gate (similarity threshold) is your most reliable abstention tool** — trust it more than the model's promises.
- **Your journal is a deliverable**, not a diary. The offer rewards honest limits analysis as much as performance.
- **Be willing to cut the stretch goal without guilt.** A well-evaluated French Code-du-travail assistant is a complete, defensible internship.
