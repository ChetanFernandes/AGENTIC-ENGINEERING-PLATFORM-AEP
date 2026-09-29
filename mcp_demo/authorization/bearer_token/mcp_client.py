from langchain.mcp import MCPAdapter
from fastmcp import Client
import os
from dotenv import load_dotenv
load_dotenv()
from langchain.agents import create_agent
from config.llm_config import llm_openai
import asyncio
from mcp_demo.authorization.run_oauth import main as start_oauth_flow
from langchain.messages import AIMessage, ToolMessage

#token = os.getenv("MCP_AUTH_TOKEN")

token = start_oauth_flow()

client = Client("http://127.0.0.1:8000/mcp",auth=token)

adapter = MCPAdapter(client)

async def main():
   tools = await adapter.list_tools()
   print(tools)
   agent = create_agent(model =llm_openai,tools = tools,)
   result = await agent.ainvoke({"messages" : [{"role" : "user" , "content": "Give me details of user 'Chetan'. Call tool get_user() "}]})
   for message in result["messages"]:
      if isinstance(message, AIMessage):
         print("AI_message",message.content)
         print("Tool_call",message.tool_calls)
      if isinstance(message,ToolMessage) and message.artifact is not None:
         structured = message.artifact["structured_content"]
         print(f"Structured content: {structured}")
         print("Tool_Message",message.content)
   print(result)

if __name__ == "__main__":
    asyncio.run(main())


    


'''
1. Resource Owner
   ↓
   The user

2. Client (Outh client)
   ↓
   Your AEP

3. Authorization Server (FastMCP OAuthProvider)
   ↓
   Authenticates the user and issues an access token

4. Resource Server
   ↓
   Your MCP server
   Validates the access token
'''
''' 
User
 │
 │ 1. Wants to use protected MCP
 ▼
Authorization Server
 │
 │ 2. Authenticates user
 │
 │ 3. User grants permission
 │
 │ 4. Returns access token
 ▼
AEP / MCP Client
 │
 │ 5. Authorization: Bearer <access_token>
 ▼
MCP Server
 │
 │ 6. Validates token
 ▼
MCP Tool
'''