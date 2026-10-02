# 🧠 Multi-Agent Research Pipeline

> Give it a topic. Watch four AI agents — search, read, write, and critique — hand work off to each other in real time.

Most "AI research tools" are a single prompt wearing a trench coat. This isn't that. This is four distinct agents, each with one job, coordinating through a live streaming pipeline — and you get to watch it happen, not just wait for a spinner to disappear.

**[Live Demo](https://research-agent-pipeline.vercel.app)** · **[Repo](https://github.com/myoohit/Multi-Agent-System)** · **[Evaluation results](#evaluation)**

---

## What it actually does

You type a topic. Behind the scenes, four agents run in sequence, each handing its output to the next:

| # | Agent | Job |
|---|---|---|
| 1 | 🔎 **Search Agent** | Fires exactly one live web search (via Tavily) — never answers from its own memory |
| 2 | 📖 **Reader Agent** | Picks the most relevant result and scrapes it for the real, detailed content |
| 3 | ✍️ **Writer Chain** | Synthesizes both into a structured report: introduction, key findings, conclusion, sources |
| 4 | 🧐 **Critic Chain** | Reviews the report like a peer reviewer would, and scores it out of 10 |

Every step streams to the frontend the moment it finishes — no fake loading bar, no "please wait." You watch the pipeline diagram light up node by node, in real time, because that's literally what's happening on the server. When it's done, download the whole thing as a clean, research-paper-styled PDF.

---

## Why this exists

Most agent demos either (a) fake the "multi-agent" part with one LLM call and a system prompt, or (b) actually build something real but hide all the mechanics behind a spinner so you have no idea what's going on underneath. I wanted neither.

This project was built to answer one question properly: **what does it actually take to turn a working agent pipeline into something that streams live to a browser, end to end, without pretending the hard parts don't exist?**

Along the way, that meant solving real, unglamorous problems — not just "prompt an LLM and hope":

- LangChain agents don't return one clean answer, they return a full message transcript — and the model's own "summary" of a tool's output can silently drop details like URLs. Had to learn to reach past that and pull the raw tool output directly.
- An LLM judging another LLM's work isn't neutral — the critic agent kept flagging real, current events as "hallucinated" simply because they were after its own training cutoff. Had to explicitly design around the judge's blind spot, not just the model being judged.
- Turning a synchronous, `return`-once pipeline into something that streams incrementally meant learning how Python generators and Server-Sent Events actually work together — not just wiring up a library and hoping.
- Once it worked, "it looks good" wasn't a good enough answer. I built an eval harness to measure it — and found the pipeline's own Critic couldn't tell a faithful report from a made-up one. See [Evaluation](#evaluation).

---

## System architecture

```
┌────────────────────┐                                    ┌──────────────────────────┐
│                     │   GET /research?topic=...          │                          │
│   React Frontend    │ ──────────────────────────────────▶│    FastAPI Backend       │
│   (Vercel)          │                                    │    (Render)              │
│                     │◀────────────────────────────────── │                          │
└─────────────────────┘   SSE stream: one event per step   └────────────┬─────────────┘
                                                                          │
                                                            stream_research_pipeline()
                                                                          │
                    ┌───────────────────┬──────────────────┬─────────────┴──────┐
                    ▼                   ▼                  ▼                    ▼
             ┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
             │ Search Agent│───▶│ Reader Agent │───▶│ Writer Chain │───▶│ Critic Chain │
             │  + Tavily   │    │+ BeautifulSoup│   │  (LLM only)  │    │  (LLM only)  │
             └─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                              all four powered by Groq (gpt-oss-20b)

                                            │
                                            ▼
                              ┌──────────────────────────┐
                              │   POST /download-pdf      │
                              │   markdown → HTML → PDF   │
                              │   (xhtml2pdf)              │
                              └──────────────────────────┘
```

The pipeline logic itself is completely decoupled from how it's exposed:

- **`pipeline.py`** — the original, synchronous, CLI-runnable version. Runs all 4 steps, returns one final dict. The eval harness runs this version.
- **`streaming_pipeline.py`** — wraps the *exact same* agent calls in a generator that `yield`s progress after every step. No logic duplicated, just a different delivery mechanism.
- **`main.py`** — turns that generator into a live Server-Sent Events stream that the browser's native `EventSource` API consumes directly, no client library needed.

---

## Request lifecycle — what happens when you hit "Run"

```
 1. User types a topic, clicks Run
        │
        ▼
 2. Frontend opens EventSource → GET /research?topic=...
        │
        ▼
 3. FastAPI starts streaming — connection stays open
        │
        ▼
 4. yield {"step": "search", "status": "running"}  ──▶  UI: search node turns amber
        │
        ▼
 5. Search agent calls Tavily, gets results
        │
        ▼
 6. yield {"step": "search", "status": "done", "data": ...}  ──▶  UI: search node turns cyan
        │
        ▼
 7. Steps 4–6 repeat for reader → writer → critic
        │
        ▼
 8. yield {"step": "pipeline", "status": "complete"}  ──▶  frontend closes the connection
        │
        ▼
 9. Report + critique render as formatted markdown
        │
        ▼
10. (optional) User clicks Download PDF → POST /download-pdf → PDF bytes returned → browser downloads file
```

No polling, no waiting for the whole pipeline to finish before seeing anything — the UI updates the instant each agent does.

---

## API reference

| Endpoint | Method | Description |
|---|---|---|
| `/research` | `GET` | Query param `topic`. Returns a `text/event-stream` — one SSE event per pipeline step. |
| `/download-pdf` | `POST` | JSON body: `{ topic, report, critique }`. Returns raw PDF bytes with a `Content-Disposition` header for browser download. |

**Example SSE event:**
```json
{"step": "search", "status": "done", "data": "Title: ...\nURL: ...\nSnippet: ..."}
```

---

## Evaluation

"It looks good" isn't evidence, so the repo includes an eval harness that runs the pipeline on a fixed set of questions and scores every report.

### What it measures

| Metric | How it's computed |
|---|---|
| **Faithfulness** (1–5) | An independent LLM judge checks whether each factual claim in the report is backed by the search results and scraped page the Writer actually saw |
| **Completeness** (1–5) | The same judge scores coverage of the topic, specificity, and required sections |
| **URL grounding** (0–1) | Share of URLs cited in the report that actually appear in the retrieved research (catches invented sources) |
| **Critic score** (1–10) | The pipeline's own Critic score, parsed from its output — kept so it can be compared against the independent judge |
| **Latency / failure rate** | Wall-clock time per run; share of runs that crashed |

The test set is 20 questions in `evals/queries.json`, split into four categories: **easy** (well-documented topics), **ambiguous** (open-ended or opinion-style), **niche** (technical and logistics topics), and **recent** (current events). The judge is a different, larger model from the one that writes the reports (`openai/gpt-oss-120b` vs `openai/gpt-oss-20b`).

### Run it

```bash
python run_evals.py --tag baseline                       # full run (~15 min)
python run_evals.py --limit 3 --tag smoke                # quick smoke test
python run_evals.py --ids 4,8,12 --tag writer-v2         # re-run chosen queries
python run_evals.py --rejudge evals/results/<file>.json  # re-score a saved run without re-running the pipeline
python run_evals.py --compare evals/results/A.json evals/results/B.json
```

Results (every report, every score, plus a summary) are saved to `evals/results/`.

### Baseline results

19 of 20 queries completed. One failed on Groq's daily token limit, not a pipeline error.

| Group | Faithfulness | Completeness | Critic score | URL grounding | Latency |
|---|---|---|---|---|---|
| **Overall** | **3.2 / 5** | **4.5 / 5** | **6.8 / 10** | **0.98** | **51 s** |
| Easy | 3.6 | 4.8 | 6.6 | 1.00 | 41 s |
| Ambiguous | 2.8 | 4.6 | 6.8 | 0.97 | 52 s |
| Niche | 3.0 | 4.4 | 7.0 | 0.97 | 57 s |
| Recent | 3.5 | 4.3 | 6.8 | 1.00 | 56 s |

### What it found

1. **The reports are complete and the sources are real, but many claims aren't supported.** Completeness is high and almost every cited URL is genuine, yet faithfulness averages 3.2/5.
2. **The Writer invents statistics.** On several queries (social media effects, carrier allocation, RAG chunking) the report contained precise percentages and named studies that appear nowhere in the retrieved research. The Writer prompt asks for "specific numbers, percentages, and dates" and a minimum of three findings, which likely pushes the model to fill gaps when the sources are thin.
3. **The built-in Critic doesn't notice.** It gave 6 or 7 out of 10 to almost every report, whether the independent judge scored faithfulness 1 or 5 (correlation ≈ 0.08 across 19 reports). The Critic only receives the report, never the sources, so it has nothing to check claims against.

### Limitations

- **Small sample.** 20 queries and a single run per query: a useful signal for before-and-after comparisons, not a statistical benchmark.
- **Same model family.** The judge and the Writer both come from the GPT-OSS family, so the judge may be more lenient than an independent one would be.
- **Strict grounding standard.** The judge only credits claims the retrieved sources support. Some penalized claims were true general knowledge the Writer added from memory (e.g. TCP's three-way handshake), which is a different failure from invented statistics.
- **Judge context cap.** The judge sees the first 12,000 characters of the source material, which can be less than the Writer saw on long pages.
- **Judge not hand-validated at scale.** Scores were spot-checked on a handful of reports, not audited across the whole set.

### Next steps

- Rewrite the Writer prompt so numbers and studies may only come from the retrieved research, and allow fewer than three findings when the sources are thin. Re-run the weakest queries, then the full set, and compare against the baseline.
- Give the Critic access to the sources so it can check claims, then test whether a Writer-revises-after-Critic step improves faithfulness.
- Parallelize the Reader across multiple URLs and measure the faithfulness gain against the added latency.

---

## Tech stack

| Layer | Tools |
|---|---|
| **Agents & orchestration** | LangChain, Groq (gpt-oss-20b) |
| **Search / scraping** | Tavily API, BeautifulSoup |
| **Backend** | FastAPI, Server-Sent Events (SSE) |
| **PDF generation** | xhtml2pdf, Python-Markdown |
| **Frontend** | React, Vite |
| **Evaluation** | LLM-as-judge (Groq, gpt-oss-120b), custom Python harness |
| **Containerization** | Docker (backend image), Docker Compose |
| **Deployment** | Render (backend) · Vercel (frontend) |

---

## Project structure

```
Multi-Agent-System/
├── agents.py               # Agent + chain definitions (search, reader, writer, critic)
├── tools.py                 # web_search (Tavily) and scrape_url (BeautifulSoup)
├── pipeline.py               # Original synchronous pipeline (CLI-runnable)
├── streaming_pipeline.py     # Same pipeline, wrapped as a generator for SSE
├── pdf_generator.py          # Markdown → styled, downloadable PDF
├── debug_search.py           # Standalone script for testing search/scrape tools in isolation
├── main.py                   # FastAPI app: /research (SSE) + /download-pdf
├── run_evals.py              # Eval harness: runs the pipeline on a query set and scores it
├── Dockerfile                # Container image for the FastAPI backend
├── docker-compose.yml        # One-command local run of the backend container
├── .dockerignore             # Keeps secrets, .venv and the frontend out of the image
├── requirements.txt
│
├── evals/
│   ├── queries.json          # 20 test questions (easy / ambiguous / niche / recent)
│   └── results/              # Saved eval runs (reports, scores, summaries)
│
└── frontend/
    └── src/
        ├── App.jsx               # SSE connection + state management
        ├── components/
        │   ├── Hero.jsx            # Topic input + run button
        │   ├── PipelineDiagram.jsx # Live 4-agent status visualization
        │   ├── OutputPanel.jsx     # Rendered report, critique, PDF download
        │   ├── InfoSection.jsx     # "How it works" explainer
        │   └── Footer.jsx
        └── index.css              # Design tokens + typography
```

---

## Running it locally

**Backend** (run from the repo root)
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the repo root:
```
GROQ_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
```

```bash
uvicorn main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
```

Create a `.env` file in `frontend/`:
```
VITE_API_URL=http://localhost:8000
```

```bash
npm run dev
```

Open `http://localhost:5173`, type a topic, hit Run.

---

## Running the backend with Docker

The backend ships with a Dockerfile, so you can run it without installing Python or a virtual environment — just Docker.

```bash
# build the image (from the repo root)
docker build -t research-agent-backend .

# run it, passing API keys from your .env at runtime
docker run --rm -p 8000:8000 --env-file .env research-agent-backend
```

Or, with Docker Compose:

```bash
docker compose up --build
```

Then open `http://localhost:8000/docs` to check the API is up, and run the frontend as described above with `VITE_API_URL=http://localhost:8000`.

A few notes:

- **Secrets stay out of the image.** `.dockerignore` excludes `.env`; the keys are passed in at runtime with `--env-file`.
- **No quotes in `.env` when using Docker.** `--env-file` passes quote characters through literally, so write `GROQ_API_KEY=abc123`, not `GROQ_API_KEY="abc123"`.
- **Port.** The container listens on `$PORT` if it's set, otherwise on 8000.
- **Backend only.** The frontend is built and deployed separately on Vercel, so it isn't part of the image.

---

## Environment variables

| Variable | Where | Description |
|---|---|---|
| `GROQ_API_KEY` | Backend `.env` | Auth key for Groq (runs the LLM — gpt-oss-20b) |
| `TAVILY_API_KEY` | Backend `.env` | Auth key for Tavily's search API |
| `JUDGE_MODEL` | Backend `.env` (optional) | Model used by the eval judge. Defaults to `openai/gpt-oss-120b` |
| `VITE_API_URL` | Frontend `.env` | URL the frontend calls — `localhost:8000` in dev, the deployed Render URL in prod |

---

## A few deliberate design decisions

**Why four separate agents instead of one big prompt?**
Because each stage has a genuinely different job and different failure mode. A single mega-prompt trying to search, synthesize, *and* self-critique in one pass tends to blur all three together — the model can't meaningfully critique work it just produced in the same breath. Splitting them into distinct agents with narrow, single-purpose system prompts makes each one easier to reason about, debug, and improve independently.

**Why Server-Sent Events instead of WebSockets?**
The data only ever flows one direction — server to client. SSE is simpler than WebSockets for exactly this case, rides over plain HTTP (friendlier to most hosting setups), and the browser's native `EventSource` API handles reconnection and message parsing without a client-side library.

**Why does the reader agent scrape raw HTML instead of just trusting the search snippet?**
Search snippets are short and often miss the actual substance of an article. The reader agent goes one level deeper — picks the most relevant result and pulls the real page content — so the writer has more than a 300-character teaser to work with.

**Why pull the raw `ToolMessage` instead of the agent's final answer?**
`create_agent()` returns the full message transcript of its internal loop, and the last message is the model's own summary of the tool's output — which can silently drop or reword details like URLs. The pipeline walks the message list backwards and grabs the raw, untouched tool output instead, so sources stay exact.

**Why an independent judge instead of trusting the Critic agent?**
The Critic only sees the finished report, not the sources behind it, so it can judge writing quality but not whether claims are true. The eval harness uses a separate, larger model that is shown both the sources and the report, and the baseline run confirmed the difference: the Critic's scores barely moved while faithfulness ranged from 1 to 5.

**What would I change with more time?**
Fix the invented-statistics problem the evals exposed (stricter Writer prompt, sources visible to the Critic), add per-step error handling in the streaming pipeline (right now a failed step kills the whole SSE connection with no graceful message to the user), and parallelize the reader agent across multiple URLs instead of just one — measuring each change against the baseline.

---

## License

MIT — do whatever you want with it.