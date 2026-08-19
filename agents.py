from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search,scrape_url
import os
from dotenv import load_dotenv

load_dotenv()


#model setup
llm = ChatGroq(
    model="qwen/qwen3.6-27b",
    temperature=0,
    reasoning_effort="none",
    max_retries=5  # auto-retries on rate limits instead of crashing
)


# 1st agent - always searches the web, never answers from its own memory
def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt=(
            "You are a research search agent. Call the web_search tool exactly ONCE "
            "with a single clear query covering the topic, then immediately write your "
            "final answer using the tool's results. Never call the tool more than once. "
            "Your own training data can be outdated - trust the tool's results, not your "
            "memory. Return the raw results (titles, URLs, snippets) as-is, don't drop URLs."
        )
    )


def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt=(
            "You are a research reader agent. Pick the most relevant URL from the given "
            "search results and call scrape_url exactly ONCE, then immediately write your "
            "final answer using the result. Never call the tool more than once."
        )
    )
#write chain
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Rules:
- Use specific numbers, percentages, and dates from the research wherever available.
- When you state a claim, mention which source it came from.
- IMPORTANT: The research may contain results from DIFFERENT policy events/dates (e.g. one article about a rate cut, another about a rate hold on a different date). Do not blend numbers or claims from different events into a single narrative. If sources describe different dates/events, treat them separately and say so clearly.
- If the exact quarter/period asked about doesn't match what's in the sources (e.g. sources cover Q3 but the topic asks about Q4), say so explicitly instead of silently relabeling the data.
- Be detailed, factual and professional."""),
])

writer_chain=writer_prompt | llm | StrOutputParser()


#critic_chain
critic_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a sharp and constructive research critic. Be honest and specific. "
     "Today's date is August 2026. Your own training data has a cutoff before this date, "
     "so you will not personally recognize many 2026 events - that does NOT make them fake. "
     "The report you're reviewing is built from live web search results with real URLs from "
     "real domains (wsj.com, cnbc.com, etc) - treat these as legitimate unless the report text "
     "itself is internally inconsistent. Do NOT deduct points, call something 'hallucinated', "
     "or question a source's existence just because you don't personally recall the event or "
     "because it's dated after your training cutoff. Judge the report only on: clarity, "
     "structure, whether claims are properly tied to sources, internal consistency, and writing quality."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()
