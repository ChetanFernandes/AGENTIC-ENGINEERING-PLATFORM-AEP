from app.executor.langgraph.graph import AgentExecutor
from app.schemas.custom_schemas import RuntimeContextSchema
from logger.log import setup_logging
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from config.database_config import DB_URI
log = setup_logging()

class ServiceLayer:
    def __init__(self):
        self.agent_executor = AgentExecutor()
        self.checkpointer = None

    async def initialize_mcp_checkpointer(self):
        await self.agent_executor.mcp_manager.start()

        # Start async Postgres checkpointer
        self.agent_executor.checkpointer_context = await self.agent_executor.exit_stack.enter_async_context(AsyncPostgresSaver.from_conn_string(DB_URI))   #as creating a recipe/instruction for a database connection, not necessarily opening the connection yet.
        #self.checkpointer = await self.checkpointer_context.__aenter__() # Open/initialize this resource and give me the actual checkpointer."
        await self.agent_executor.checkpointer_context.setup()
        
        # Compile graph only after checkpointer is ready
        self.graph = self.agent_executor.graph.compile(self.agent_executor.checkpointer_context)

        self.checkpointer  = self.agent_executor.checkpointer_context
        log.info("MCP and Postgress server started")


    async def get_payload_data(self,user_name,thread_id,question):
        try:
            log.info("user_name:%s",user_name)
            log.info("thread_id:%s",thread_id)
            log.info("question:%s",question)
            await self.initialize_langgraph(user_name,thread_id,question)
        except Exception:
            log.exception("Error while receiving data in service layer")


    async def initialize_langgraph(self,user_name,thread_id,question):
        try:
            runtime_context = RuntimeContextSchema(user_name = user_name, checkpointer =  self.checkpointer , backend = self.agent_executor.store_backend)
            config = {"configurable" : {"thread_id": thread_id}}
            await self.graph.ainvoke( {"user_request":question}, config = config, context = runtime_context)
        except Exception:
            log.exception("Error while processing the request")





    
   
