"""
FastAPI app exposing the pipeline as a Server-Sent Events (SSE) stream.
Run locally with: uvicorn main:app --reload
"""

import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from streaming_pipeline import stream_research_pipeline
from fastapi import Body
from fastapi.responses import Response
from pdf_generator import build_report_pdf
app = FastAPI()

@app.post("/download-pdf")
def download_pdf(payload: dict = Body(...)):
    topic = payload.get("topic", "Research Report")
    report = payload.get("report", "")
    critique = payload.get("critique")

    pdf_bytes = build_report_pdf(topic, report, critique)

    # Safe filename: strip spaces/odd characters, cap length
    safe_name = "".join(c if c.isalnum() or c in " -_" else "" for c in topic).strip().replace(" ", "_")[:50]

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}_report.pdf"'},
    )

# CORS: your React app runs on a different origin (localhost:5173 in dev,
# your-app.vercel.app in prod) than this API, so the browser will block
# requests unless we explicitly allow it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://multi-agent-system-alpha.vercel.app"],  # tighten this to your actual Vercel URL once deployed
    allow_methods=["*"],
    allow_headers=["*"],
)


def sse_event_stream(topic: str):
    """
    Wraps stream_research_pipeline() and formats each event the way the
    SSE spec expects: "data: <json>\n\n" per message.
    """
    for event in stream_research_pipeline(topic):
        yield f"data: {json.dumps(event)}\n\n"


@app.get("/research")
def research(topic: str):
    return StreamingResponse(
        sse_event_stream(topic),
        media_type="text/event-stream",
    )