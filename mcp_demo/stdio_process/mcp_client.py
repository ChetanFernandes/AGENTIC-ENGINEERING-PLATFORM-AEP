from langchain.mcp import MCPAdapter
from pathlib import Path
import asyncio
from langchain.agents import create_agent
from config.llm_config import llm_openai

adapter = MCPAdapter(Path(r"D:\Agentic Engineering Platform — Project Plan\AEP\mcp_demo\stdio_process\stdio_process.py"))

async def main():
    tools = await adapter.list_tools()
    #print(tools)
    agent = create_agent(model = llm_openai , tools= tools,system_prompt = "Use the addition tool to add  10 and 20")
    result = await agent.ainvoke({"messages" :  [{"role":"user" , "content" : "a = 10 , b = 20"}]

                 })
    print(result["messages"][-1].content)


if __name__=="__main__":
    asyncio.run(main())
