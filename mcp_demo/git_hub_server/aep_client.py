from langchain.mcp import MCPAdapter
from fastmcp import Client
import asyncio
from dotenv import load_dotenv
load_dotenv()
import os
from langchain.agents import create_agent
from config.llm_config import llm_openai
from langchain.messages import AIMessage, ToolMessage

token = os.getenv("GITHUB_ACCESS_TOKEN")

client = Client("https://api.githubcopilot.com/mcp/", auth = token)

mcp = MCPAdapter(client)

async def main():
    tools = await mcp.list_tools()
    print([tool.name for tool in tools])
    #get_me_tool = next(tool for tool in tools if tool.name == "get_me")
    #result = await get_me_tool.ainvoke({})
    #print(result)
    #agent = create_agent(model = llm_openai,tools = tools)
    #result = await agent.ainvoke({"messages" : [{"role":'user', "content": "Tell me about my GitHub profile."}]})
    #print(result)
    #for message in result["messages"]:
        #if isinstance(message, AIMessage):
            #print("AI_message",message.content)
            #print("Tool_call",message.tool_calls)
        #if isinstance(message,ToolMessage):
            #print("Tool_Message",message.content)



if __name__=="__main__":
    asyncio.run(main())