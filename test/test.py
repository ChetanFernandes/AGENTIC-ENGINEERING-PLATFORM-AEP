import asyncio
import os
from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.auth import BearerAuth
from langchain.mcp import MCPAdapter

load_dotenv()

async def main():
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not token:
        raise ValueError("GITHUB_ACCESS_TOKEN is missing")

    client = Client(
        "https://api.githubcopilot.com/mcp/",
        auth=BearerAuth(token),
        mode="auto",
    )

    adapter = MCPAdapter(client)

    async with adapter as session:
        print("MCPAdapter connection successful")
        tools = await session.list_tools()
        print("Number of tools:", len(tools))
        print("First 10 tools:", [tool.name for tool in tools[:10]])

asyncio.run(main())