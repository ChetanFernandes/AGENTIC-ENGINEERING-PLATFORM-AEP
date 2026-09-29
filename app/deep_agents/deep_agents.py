from deepagents import create_deep_agent
from llm_config import llm_openai 



internet_search = {"type" : "web_search"}

research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""

agent = create_deep_agent(model = llm_openai, tools = [internet_search], system_prompt = research_instructions )

agent.invoke(
                {"messages" : [{ 
                                "role":"user",
                                "content" : "Research REST APIs. First understand what REST is, then compare REST with SOAP, then identify when REST should be preferred, and finally produce a concise recommendation"
                                }]
                }
            )



