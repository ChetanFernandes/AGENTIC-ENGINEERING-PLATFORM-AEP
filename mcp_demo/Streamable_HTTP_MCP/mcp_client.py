from langchain.mcp import MCPAdapter
import asyncio
from langchain.agents import create_agent
from config.llm_config import llm_openai

mcp = MCPAdapter("http://127.0.0.1:8000/mcp")

async def main():
    tools = await mcp.list_tools()
    print(tools)
    agent = create_agent(model =llm_openai,tools = tools,)
    result = await agent.ainvoke({"messages" : [{"role" : "user" , "content" : "a= 10 , b = 40"}]})
    print(result["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())