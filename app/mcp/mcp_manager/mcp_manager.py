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
from logger.log import setup_logging
log = setup_logging()

@dataclass
class MCPSessionEntry():
    server_name: str
    client:object
    adapter:object
    session:object
    tools:list
    protocol_version: str | None
    exit_stack: AsyncExitStack

class MCPManager():

    def __init__(self, pool_size:int = 1):
        #client_group, client_factories:dict

        self.pool_size = pool_size

        def create_github_client():
            return Client("https://api.githubcopilot.com/mcp/", auth=token,  mode="auto")
        
        self.client_factories = {"github_1": create_github_client, "github_2": create_github_client,}

        self.server_groups = {"github": ["github_1", "github_2",]}


        self.client_group = ClientGroup({"github_1":create_github_client(),"github_2":create_github_client()}) 
        # ClientGroup is the source of registered MCP servers 

        self.pool_size = pool_size

        self.tools_cache = {}
        self.session_pools = {}
        self.searchable_tools = []
        # Used to notify waiting acquire() calls
        # when a session is released back to a pool.
        self.pool_condition = asyncio.Condition()


    async def _create_session(self,server_name:str) -> MCPSessionEntry:
        log.info("MCP SESSION CREATE START | server=%s", server_name)

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

        log.info("MCP SESSION CREATE SUCCESS | server=%s",server_name)

        return MCPSessionEntry(
            server_name = server_name,
            client=client,
            adapter=adapter,
            session=session,
            tools=tools,
            protocol_version=client.protocol_version,
            exit_stack=exit_stack
        )


    async def start(self):
        """
        Create connection pools for every physical MCP server.

        Example with pool_size=2:

            github_1 -> [S1, S2]
            github_2 -> [S1, S2]
        """
        log.info("MCP MANAGER START | pool_size=%s", self.pool_size)
        for server_name in self.client_group.clients: # Python treats iteration over a dictionary as iteration over its keys.
            # Pool for this server
            log.info("MCP POOL CREATE | server=%s | pool_size=%s", server_name, self.pool_size)
            queue = asyncio.Queue(maxsize=self.pool_size) # This one creates empty box
            # Create N independent clients/sessions
            for _ in range(self.pool_size):
                entry = await self._create_session(server_name)
                await queue.put(entry)

            self.session_pools[server_name] = queue
            log.info("MCP POOL READY | server=%s | available=%s", server_name, queue.qsize())

        log.info("MCP MANAGER START COMPLETE")

            

    async def acquire(self,logical_server_name: str) -> MCPSessionEntry:

        """
        Acquire an available MCP session for a logical server.

        Example:
            await manager.acquire("github")

        The manager checks all physical servers mapped to
        the logical server and returns the first available session.

        If all physical servers are busy, it waits until a
        session is released.
        """

        if logical_server_name not in self.server_groups:
            raise ValueError(
                f"Unknown logical MCP server: "
                f"{logical_server_name}"
            )

        physical_servers = self.server_groups[
            logical_server_name
        ]

        log.info(
            "MCP ACQUIRE START | logical_server=%s | "
            "physical_servers=%s",
            logical_server_name,
            physical_servers
        )

        async with self.pool_condition:

            while True:

                # Check all physical servers for an
                # immediately available session.
                for server_name in physical_servers:

                    queue = self.session_pools[server_name]

                    try:
                        session_entry = queue.get_nowait()

                    except asyncio.QueueEmpty:
                        continue

                    log.info(
                        "MCP ACQUIRE SUCCESS | "
                        "logical_server=%s | "
                        "physical_server=%s | "
                        "available_after=%s",
                        logical_server_name,
                        server_name,
                        queue.qsize()
                    )

                    return session_entry

                # All physical servers are currently busy.
                log.info(
                    "MCP ACQUIRE WAIT | "
                    "logical_server=%s | "
                    "all physical servers busy",
                    logical_server_name
                )

                # Wait until release() notifies us that
                # a session has become available.
                await self.pool_condition.wait()


    async def release(self,session_entry:MCPSessionEntry):
        """
        Return a session to the physical server pool from which
        it originally came.

        The agent does NOT need to know the physical server.
        """
        server_name = session_entry.server_name

        if server_name not in self.session_pools:
             raise ValueError(
                f"Unknown physical server: {server_name}"
            )

        queue = self.session_pools[server_name]
        async with self.pool_condition:
            await queue.put(session_entry)
            log.info(
                "MCP RELEASE | physical_server=%s | available=%s",
                server_name,
                queue.qsize()
            )
            # Wake up agents waiting for ANY session.
            self.pool_condition.notify_all()


    async def discard_and_replace(self,session_entry:MCPSessionEntry):
        """
        Close a broken MCP connection and create a replacement
        connection in the same physical server pool.
        """
        server_name = session_entry.server_name
        log.warning(
            "MCP DISCARD SESSION | server=%s",
            server_name
        )

        # Close the broken conenction
        try:
            await session_entry.exit_stack.aclose()
        except Exception:

            log.exception(
                "MCP SESSION CLOSE FAILED | server=%s",
                server_name
            )

        # Create a completely new connection
        replacement = await self._create_session(server_name)

        # --------------------------------------------------
        # Return replacement to same physical pool
        # --------------------------------------------------
        async with self.pool_condition:

            # Return replacement to the pool
            await self.session_pools[server_name].put(replacement)
            log.info(
                "MCP SESSION REPLACED | server=%s | available=%s",
                server_name,
                self.session_pools[
                    server_name
                ].qsize()
            )
          # Wake agents waiting for a session.
            self.pool_condition.notify_all()


    async def close(self):
        """
        Close all currently available MCP sessions.

        Sessions currently checked out by agents must first be
        released before they can be closed by this method.
        """
        log.info("MCP MANAGER CLOSE START")

        for server_name, queue in self.session_pools.items():

            log.info(
                "MCP POOL CLOSE | server=%s | available=%s",
                server_name,
                queue.qsize()
            )

            while not queue.empty():

                session_entry = await queue.get()

                try:

                    await session_entry.exit_stack.aclose()

                    log.info(
                        "MCP SESSION CLOSED | server=%s",
                        server_name
                    )

                except Exception:

                    log.exception(
                        "MCP SESSION CLOSE FAILED | server=%s",
                        server_name
                    )






''' 

MCP Server: github_1
        ↓
    Connection Pool
        ↓
 ┌──────┬──────┬──────┐
 │ S1   │ S2   │ S3   │
 └──────┴──────┴──────┘
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