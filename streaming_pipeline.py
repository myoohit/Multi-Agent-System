"""
Thin streaming wrapper around the existing run_research_pipeline().
This file does NOT reimplement any agent logic — it just calls the
exact same functions from agents.py, in the exact same order that
pipeline.py already uses, but yields progress after each step instead
of returning everything at the end.
"""

from agents import build_search_agent, build_reader_agent, writer_chain, critic_chain
from pipeline import get_tool_result, strip_think  # reusing your existing helpers as-is


def stream_research_pipeline(topic: str):
    """
    A generator function. Each `yield` sends one JSON-serializable dict
    describing what just happened. The FastAPI layer (next piece) will
    forward each yielded dict to the frontend as it happens.

    Every event has:
      - "step": which of the 4 agents this is about
      - "status": "running" (about to start) or "done" (finished)
      - "data": the actual output (only present when status == "done")
    """

    state = {}

    # ---- Step 1: Search agent ----
    yield {"step": "search", "status": "running"}

    search_agent = build_search_agent()
    search_result = search_agent.invoke(
        {"messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]},
        config={"recursion_limit": 25}
    )
    state["search_results"] = get_tool_result(search_result)

    yield {"step": "search", "status": "done", "data": state["search_results"]}

    # ---- Step 2: Reader agent ----
    yield {"step": "reader", "status": "running"}

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke(
        {"messages": [("user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results'][:1500]}"
        )]},
        config={"recursion_limit": 25}
    )
    state["scraped_content"] = get_tool_result(reader_result)

    yield {"step": "reader", "status": "done", "data": state["scraped_content"]}

    # ---- Step 3: Writer chain ----
    yield {"step": "writer", "status": "running"}

    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )
    state["report"] = strip_think(writer_chain.invoke({
        "topic": topic,
        "research": research_combined
    }))

    yield {"step": "writer", "status": "done", "data": state["report"]}

    # ---- Step 4: Critic chain ----
    yield {"step": "critic", "status": "running"}

    state["feedback"] = strip_think(critic_chain.invoke({
        "report": state["report"]
    }))

    yield {"step": "critic", "status": "done", "data": state["feedback"]}

    # Final event so the frontend knows the whole pipeline finished
    yield {"step": "pipeline", "status": "complete"}