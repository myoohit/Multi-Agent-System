from agents import build_search_agent

agent = build_search_agent()

for step in agent.stream(
    {"messages": [("user", "Find recent info about: RBI repo rate impact on Nifty Bank index")]},
    config={"recursion_limit": 20}
):
    print(step)
    print("-----")