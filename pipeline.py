import re
from langchain_core.messages import ToolMessage
from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain


def get_tool_result(agent_response: dict) -> str:
    """
    create_agent() returns a list of messages, not just the tool output.
    The last message is the AI's own summary (can drop details like URLs).
    So we search backwards and grab the actual ToolMessage instead -
    that's the raw, untouched tool output.
    """
    for msg in reversed(agent_response["messages"]):
        if isinstance(msg, ToolMessage):
            return msg.content
    return agent_response["messages"][-1].content  # fallback, just in case


def strip_think(text: str) -> str:
    """Safety net - removes any leftover <think>...</think> block from output."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def run_research_pipeline(topic: str) -> dict:

    state = {}

    # step 1 - search agent
    print("\n" + " ="*50)
    print("step 1 - search agent is working ...")
    print("="*50)

    search_agent = build_search_agent()
    search_result = search_agent.invoke(
    {"messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]},
    config={"recursion_limit": 25}
)
    state["search_results"] = get_tool_result(search_result)  # raw output, URLs included

    print("\n search result ", state['search_results'])

    # step 2 - reader agent
    print("\n" + " ="*50)
    print("step 2 - Reader agent is scraping top resources ...")
    print("="*50)

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke(
        {"messages": [("user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results'][:1500]}"
        )]},
        config={"recursion_limit": 25}
    )
    
    state['scraped_content'] = get_tool_result(reader_result)  # raw scraped text, not AI summary

    print("\nscraped content: \n", state['scraped_content'])

    # step 3 - writer chain
    print("\n" + " ="*50)
    print("step 3 - Writer is drafting the report ...")
    print("="*50)

    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )

    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": research_combined
    })
    state["report"] = strip_think(state["report"])  # clean up any stray reasoning text

    print("\n Final Report\n", state['report'])

    # step 4 - critic
    print("\n" + " ="*50)
    print("step 4 - critic is reviewing the report ")
    print("="*50)

    state["feedback"] = critic_chain.invoke({
        "report": state['report']
    })
    state["feedback"] = strip_think(state["feedback"])

    print("\n critic report \n", state['feedback'])

    return state


if __name__ == "__main__":
    topic = input("\n Enter a research topic : ")
    run_research_pipeline(topic)