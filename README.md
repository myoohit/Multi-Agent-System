# 🧠 Multi-Agent Research Pipeline

> Give it a topic. Watch four AI agents — search, read, write, and critique — hand work off to each other in real time.

Most "AI research tools" are a single prompt wearing a trench coat. This isn't that. This is four distinct agents, each with one job, coordinating through a live streaming pipeline — and you get to watch it happen, not just wait for a spinner to disappear.

**[Live Demo](https://research-agent-pipeline.vercel.app)** · **[Repo](https://github.com/myoohit/Multi-Agent-System)**

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
                                    all four powered by Groq (Qwen)

                                            │
                                            ▼
                              ┌──────────────────────────┐
                              │   POST /download-pdf      │
                              │   markdown → HTML → PDF   │
                              │   (xhtml2pdf)              │
                              └──────────────────────────┘
```

The pipeline logic itself is completely decoupled from how it's exposed:

- **`pipeline.py`** — the original, synchronous, CLI-runnable version. Runs all 4 steps, returns one final dict.
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

## Tech stack

| Layer | Tools |
|---|---|
| **Agents & orchestration** | LangChain, Groq (Qwen) |
| **Search / scraping** | Tavily API, BeautifulSoup |
| **Backend** | FastAPI, Server-Sent Events (SSE) |
| **PDF generation** | xhtml2pdf, Python-Markdown |
| **Frontend** | React, Vite |
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
├── requirements.txt
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

## Environment variables

| Variable | Where | Description |
|---|---|---|
| `GROQ_API_KEY` | Backend `.env` | Auth key for Groq (runs the LLM — Qwen) |
| `TAVILY_API_KEY` | Backend `.env` | Auth key for Tavily's search API |
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

**What would I change with more time?**
Per-step error handling in the streaming pipeline (right now a failed step kills the whole SSE connection with no graceful message to the user), and parallelizing the reader agent across multiple URLs instead of just one, for a more thorough report at the cost of latency.

---

## License

MIT — do whatever you want with it.
