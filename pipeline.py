from agents import build_reader_agent,build_search_agent,writer_chain,critic_chain

def run_research_pipeline(topic : str)->dict:
    state={} #main

    #search agent working
    print("\n" + "="*50)
    print("step 1 - search agent is working ....")
    print("="*50)


    search_agent=build_search_agent()
    search_result=search_agent.invoke({
        "messages":[("user",f"Find recent, reliable and detailed information about:{topic} ")]
    })
    print("\nRAW SEARCH RESULT:")
    print(search_result)


    state['search_results'] = search_result['messages'][-1].content
    print("\nSEARCH RESULT:")
    print(state['search_results'])

    print("\n search Result ",state['search_results'])

    #step 2

    print("\n" + "="*50)
    print("step 1 - Reader agent is scraping top result  ....")
    print("="*50)

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [("user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results']}"
        )] 
    })

    state['scraped_content'] = reader_result['messages'][-1].content
    
    print("\nscraped content: \n", state['scraped_content'])



    #step 3 - writer chain
    print("\n" + "="*50)
    print("step 3 -writer is drafting the report..... ")
    print("="*50)

    research_combined =(
        f"SEARCHED RESULT:\n {state['search_results']}\n\n"
        f"DETAILED SCRAPED CONTENT :\n {state['scraped_content']} "
    )

    state['report']=writer_chain.invoke({
        "topic":topic,
        "research":research_combined
    })

    print("\n Final Report \n",state['report'])

    #critic_report
    print("\n" + "="*50)
    print("step 4 -critic is reviewing the report..... ")
    print("="*50)


    state['feedback']=critic_chain.invoke({ 
        "report":state['report'],
        }
    )

    print("\n critic report \n",state['feedback'])

    return state



if __name__=="__main__":
    topic=input("\n Enter a research topic :")
    run_research_pipeline(topic)





 




