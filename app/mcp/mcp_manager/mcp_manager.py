from langchain.mcp import MCPAdapter
import asyncio
from contextlib import AsyncExitStack
from dotenv import load_dotenv
load_dotenv()
from dataclasses import dataclass
from fastmcp import Client


import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv("GITHUB_ACCESS_TOKEN")
from fastmcp.client.group import ClientGroup

@dataclass
class MCPSessionEntry():
    client:object
    adapter:object
    session:object
    tools:list
    protocol_version: str | None
    exit_stack: AsyncExitStack

class MCPManager():

    def __init__(self, client_group, client_factories:dict, pool_size:int = 1):

        def create_github_client():
            return Client("https://api.githubcopilot.com/mcp/", auth=token,  mode="auto")
        
        client_factories = {"github_1": create_github_client, "github_2": create_github_client,}

        client_group = ClientGroup({"github_1":create_github_client(),"github_2":create_github_client()})

        self.client_group = client_group

        self.client_factories = client_factories

        self.pool_size = pool_size

        self.tools_cache = {}
        self.session_pools = {}
        self.searchable_tools = []

    async def _create_session(self,server_name:str) -> MCPSessionEntry:

        # Create a NEW Client for every pool entry
        client = self.client_factories[server_name]()

        # Each connection owns its own lifecycle
        exit_stack = AsyncExitStack()

        adapter = MCPAdapter(client)

        session = await exit_stack.enter_async_context(adapter)

        #Discover tools only once per server
        if server_name not in self.tools_cache:
            tools = await session.list_tools()
            self.tools_cache[server_name] = tools
        else:
            tools = self.tools_cache[server_name]

        return MCPSessionEntry(
            client=client,
            adapter=adapter,
            session=session,
            tools=tools,
            protocol_version=client.protocol_version,
            exit_stack=exit_stack
        )


    async def start(self):
       # ClientGroup is the source of registered MCP servers 
        for server_name in self.client_group.clients: # Python treats iteration over a dictionary as iteration over its keys.
             # Pool for this server
            #print("Server_name",server_name)
            queue = asyncio.Queue(maxsize=self.pool_size) # Thsi one creates empty box
            # Create N independent clients/sessions
            for _ in range(self.pool_size):
                entry = await self._create_session(server_name)
                await queue.put(entry)

            self.session_pools[server_name] = queue

            

    async def acquire(self,server_name:str)-> MCPSessionEntry:
        session_entry = await self.session_pools[server_name].get()
        return session_entry


    async def release(self,server_name:str,session_entry:MCPSessionEntry):
        await self.session_pools[server_name].put(session_entry)


    async def discard_and_replace(self,server_name:str,session_entry:MCPSessionEntry):
        # Close the broken conenction
        await session_entry.exit_stack.aclose()

        # Create a completely new connection
        replacement = await self._create_session(server_name)

        # Return replacement to the pool
        await self.session_pools[server_name].put(replacement)

    async def close(self):
        for queue in self.session_pools.values():
            while not queue.empty():
                session_entry = await queue.get()

                await session_entry.exit_stack.aclose()

''' 

if __name__=="__main__":
   
    mcp_manager = MCPManager(client_group=None, client_factories=None, pool_size=1)
    asyncio.run(mcp_manager.start()) 
    session_entry = asyncio.run(mcp_manager.acquire("github_1"))
    from app.utilis.utilis import InterruptDefinition
    interrupt = InterruptDefinition(session_entry.tools)
    distructive_tools = interrupt.save_distructive_tools()
    print(distructive_tools)
'''




''' 
    MCPAdapter
        ↓
    ENTER
        ↓
    MCP session active
        ↓
    Agents can use tools
        ↓
    EXIT
        ↓
    MCP session cleaned up
    '''
'''

Connection reuse -Keep an existing connection and use it again.

Connection pooling - Keep multiple reusable connections and let concurrent work acquire/release them.
'''