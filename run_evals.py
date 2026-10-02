"""
Eval harness for the multi-agent research pipeline.

Put this file in the repo root (next to pipeline.py) and run from there:

    python run_evals.py --limit 3 --tag smoke      # quick test on 3 queries
    python run_evals.py --tag baseline             # full run
    python run_evals.py --category recent          # only one category
    python run_evals.py --compare evals/results/baseline_X.json evals/results/improved_Y.json

Metrics per query:
  - failed / error        did the pipeline crash?
  - latency_s             wall-clock time for the whole pipeline
  - critic_score          the pipeline's own Critic score (parsed from "Score: X/10")
  - faithfulness (1-5)    independent judge: are the report's claims backed by the
                          search results + scraped page the writer actually saw?
  - completeness (1-5)    independent judge: does it cover the topic with specifics?
  - url_grounding (0-1)   share of URLs cited in the report that appear in the
                          retrieved research (catches invented sources, no network needed)

The judge uses a DIFFERENT model from the pipeline (set JUDGE_MODEL in .env to override),
so the pipeline is not grading its own homework.
"""
import argparse
import io
import json
import os
import re
import statistics
import time
from contextlib import redirect_stdout
from datetime import datetime

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from pipeline import run_research_pipeline

load_dotenv()

QUERIES_PATH = "evals/queries.json"
RESULTS_DIR = "evals/results"

# Use a model different from the one in agents.py (openai/gpt-oss-20b).
# Check which models your Groq account offers and override with JUDGE_MODEL if needed.
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "openai/gpt-oss-120b")
judge_llm = ChatGroq(model=JUDGE_MODEL, temperature=0, max_retries=5)

JUDGE_PROMPT = """You are a strict, impartial evaluator of AI-written research reports.

You are given the SOURCE MATERIAL the writer had access to, and the REPORT it produced.
Judge ONLY against the source material. Do not use your own knowledge of the world to
accept or reject a claim: a claim counts as supported only if the source material backs it.

Score each from 1 to 5:
- faithfulness: 5 = every factual claim (numbers, dates, names) is backed by the source
  material; 3 = several unsupported or blended claims; 1 = mostly unsupported.
- completeness: 5 = covers the topic clearly with specific facts and all required
  sections (introduction, key findings, conclusion, sources); 1 = barely addresses the topic.

Respond with ONLY a JSON object and nothing else:
{"faithfulness": <1-5>, "completeness": <1-5>, "unsupported_claims": ["short description", "..."], "notes": "one sentence"}

TOPIC:
<<TOPIC>>

SOURCE MATERIAL:
<<SOURCE>>

REPORT:
<<REPORT>>
"""


def strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def parse_critic_score(feedback: str):
    m = re.search(r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", feedback or "")
    return float(m.group(1)) if m else None


def url_grounding(report: str, source_text: str):
    """Fraction of URLs in the report that also appear in the retrieved research."""
    urls = re.findall(r"https?://[^\s)\]>\"']+", report or "")
    urls = [u.rstrip(".,;:/") for u in urls]
    if not urls:
        return None
    return round(sum(1 for u in urls if u in source_text) / len(urls), 2)


def judge(topic: str, source: str, report: str) -> dict:
    prompt = (
        JUDGE_PROMPT.replace("<<TOPIC>>", topic)
        .replace("<<SOURCE>>", source[:12000])
        .replace("<<REPORT>>", report[:8000])
    )
    raw = strip_think(judge_llm.invoke(prompt).content)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        raise ValueError(f"Judge returned no JSON: {raw[:200]}")
    return json.loads(m.group(0))


def run_one(item: dict) -> dict:
    row = {"id": item["id"], "category": item["category"], "topic": item["topic"], "failed": False}
    start = time.time()
    try:
        # pipeline.py prints a lot; silence it so eval output stays readable
        with redirect_stdout(io.StringIO()):
            state = run_research_pipeline(item["topic"])
    except Exception as e:  # a crashed pipeline is a data point, not a reason to stop
        row.update(failed=True, error=repr(e)[:300], latency_s=round(time.time() - start, 1))
        return row

    row["latency_s"] = round(time.time() - start, 1)
    source = f"{state.get('search_results', '')}\n\n{state.get('scraped_content', '')}"
    report = state.get("report", "")
    row["critic_score"] = parse_critic_score(state.get("feedback", ""))
    row["url_grounding"] = url_grounding(report, source)
    row["report"] = report
    row["source"] = source[:12000]  # kept so --rejudge can re-score without re-running the pipeline
    row["critic_feedback"] = state.get("feedback", "")

    try:
        j = judge(item["topic"], source, report)
        row["faithfulness"] = j.get("faithfulness")
        row["completeness"] = j.get("completeness")
        row["unsupported_claims"] = j.get("unsupported_claims", [])
        row["judge_notes"] = j.get("notes", "")
    except Exception as e:
        row["judge_error"] = repr(e)[:300]
    return row


def mean(values):
    vals = [v for v in values if v is not None]
    return round(statistics.mean(vals), 2) if vals else None


def summarize(rows: list) -> dict:
    ok = [r for r in rows if not r["failed"]]
    return {
        "n": len(rows),
        "failure_rate": round((len(rows) - len(ok)) / len(rows), 2) if rows else None,
        "faithfulness": mean(r.get("faithfulness") for r in ok),
        "completeness": mean(r.get("completeness") for r in ok),
        "critic_score": mean(r.get("critic_score") for r in ok),
        "url_grounding": mean(r.get("url_grounding") for r in ok),
        "latency_s": mean(r.get("latency_s") for r in ok),
    }


def critic_vs_judge_correlation(rows: list):
    pairs = [
        (r["critic_score"], r["faithfulness"])
        for r in rows
        if not r["failed"] and r.get("critic_score") is not None and r.get("faithfulness") is not None
    ]
    if len(pairs) < 3:
        return None
    try:
        return round(statistics.correlation([p[0] for p in pairs], [p[1] for p in pairs]), 2)
    except statistics.StatisticsError:  # e.g. all scores identical
        return None


def print_summary(summary: dict):
    cols = ["n", "failure_rate", "faithfulness", "completeness", "critic_score", "url_grounding", "latency_s"]
    print(f"\n{'group':<12}" + "".join(f"{c:>15}" for c in cols))
    for name, s in summary["by_group"].items():
        print(f"{name:<12}" + "".join(f"{str(s[c]):>15}" for c in cols))
    print(f"\nCritic-score vs judge-faithfulness correlation: {summary['critic_vs_judge_corr']}")


def compare(path_a: str, path_b: str):
    with open(path_a, encoding="utf-8") as fa, open(path_b, encoding="utf-8") as fb:
        a, b = json.load(fa)["summary"]["by_group"]["overall"], json.load(fb)["summary"]["by_group"]["overall"]
    print(f"\n{'metric':<16}{'A':>10}{'B':>10}{'B - A':>10}")
    for k in ["failure_rate", "faithfulness", "completeness", "critic_score", "url_grounding", "latency_s"]:
        delta = round(b[k] - a[k], 2) if a[k] is not None and b[k] is not None else None
        print(f"{k:<16}{str(a[k]):>10}{str(b[k]):>10}{str(delta):>10}")


def save_results(path: str, tag: str, rows: list) -> dict:
    by_group = {"overall": summarize(rows)}
    for cat in sorted({r["category"] for r in rows}):
        by_group[cat] = summarize([r for r in rows if r["category"] == cat])
    summary = {"by_group": by_group, "critic_vs_judge_corr": critic_vs_judge_correlation(rows)}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {"tag": tag, "judge_model": JUDGE_MODEL, "summary": summary, "rows": rows},
            f, indent=2, ensure_ascii=False,
        )
    return summary


def rejudge(path: str):
    """Re-score a saved run with the current judge, without re-running the pipeline."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = data["rows"]
    for r in rows:
        if r["failed"] or not r.get("source"):
            continue
        r.pop("judge_error", None)
        try:
            j = judge(r["topic"], r["source"], r["report"])
            r["faithfulness"] = j.get("faithfulness")
            r["completeness"] = j.get("completeness")
            r["unsupported_claims"] = j.get("unsupported_claims", [])
            r["judge_notes"] = j.get("notes", "")
            print(f"[{r['id']}] faith={r['faithfulness']} compl={r['completeness']}")
        except Exception as e:
            r["judge_error"] = repr(e)[:300]
            print(f"[{r['id']}] JUDGE ERROR: {r['judge_error']}")
        time.sleep(1)
    out = path.replace(".json", "_rejudged.json")
    summary = save_results(out, data.get("tag", "run") + "_rejudged", rows)
    print_summary(summary)
    print(f"\nSaved: {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rejudge", metavar="RESULTS.json", help="re-score a saved run, no pipeline re-run")
    ap.add_argument("--tag", default="run", help="label for this run, e.g. baseline / multi-url")
    ap.add_argument("--limit", type=int, default=None, help="only run the first N queries")
    ap.add_argument("--category", default=None, help="easy | ambiguous | niche | recent")
    ap.add_argument("--ids", default=None, help="comma-separated query ids, e.g. 4,8,12,13")
    ap.add_argument("--sleep", type=float, default=2.0, help="seconds between queries (rate limits)")
    ap.add_argument("--compare", nargs=2, metavar=("A.json", "B.json"))
    args = ap.parse_args()

    if args.compare:
        compare(*args.compare)
        return
    if args.rejudge:
        rejudge(args.rejudge)
        return

    with open(QUERIES_PATH, encoding="utf-8") as f:
        queries = json.load(f)
    if args.category:
        queries = [q for q in queries if q["category"] == args.category]
    if args.ids:
        wanted = {int(x) for x in args.ids.split(",")}
        queries = [q for q in queries if q["id"] in wanted]
    if args.limit:
        queries = queries[: args.limit]

    rows = []
    out = os.path.join(RESULTS_DIR, f"{args.tag}_{datetime.now():%Y%m%d_%H%M%S}.json")
    for i, item in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] ({item['category']}) {item['topic']}")
        row = run_one(item)
        rows.append(row)
        status = "FAILED " + row.get("error", "") if row["failed"] else (
            f"faith={row.get('faithfulness')} compl={row.get('completeness')} "
            f"critic={row.get('critic_score')} urls={row.get('url_grounding')} {row['latency_s']}s"
        )
        if row.get("judge_error"):
            status += "  JUDGE ERROR: " + row["judge_error"]
        print("   ->", status)
        save_results(out, args.tag, rows)  # partial save: Ctrl+C never loses finished queries
        time.sleep(args.sleep)

    summary = save_results(out, args.tag, rows)
    print_summary(summary)
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()