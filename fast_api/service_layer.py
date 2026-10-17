from app.executor.langgraph.graph import AgentExecutor
from app.schemas.custom_schemas import RuntimeContextSchema
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from uuid import uuid4
from config.database_config import DB_URI
from app.memory.episodic_memory import EpisodicMemory
from psycopg_pool import AsyncConnectionPool
from logger.log import setup_logging
log = setup_logging()
from app.memory.schema_initializer import initialize_episodic_schema
from app.utilis.utilis import validate_user_id
from config.llm_config import llm_call

class ServiceLayer:
    def __init__(self):
        self.agent_executor = AgentExecutor()
        self.checkpointer = None
        self.db_pool = None
        self.llm_open_ai = None


    async def initialize_mcp_checkpointer(self):
        try:
            await self.agent_executor.mcp_manager.start()

            # Start async Postgres checkpointer
            self.checkpointer  = await self.agent_executor.exit_stack.enter_async_context(AsyncPostgresSaver.from_conn_string(DB_URI))   #as creating a recipe/instruction for a database connection, not necessarily opening the connection yet.
            #self.checkpointer = await self.checkpointer_context.__aenter__() # Open/initialize this resource and give me the actual checkpointer."
            await self.checkpointer.setup()

            # Episodic memory PostgreSQL pool
            self.db_pool = AsyncConnectionPool(
                                            conninfo=DB_URI,
                                            min_size=1, # keeps the pool small for this learning deployment.
                                            max_size=5, # limits concurrent database connections from this poo
                                            open=False,
                                            timeout=30, # allows up to 30 seconds to acquire a connection from the pool.
                                            kwargs={"autocommit": True},
                                        )

            await self.db_pool.open()

            # Initialize AEP episodic memory schema automatically
            await initialize_episodic_schema(self.db_pool)
            log.info("AEP episodic memory schema initialized")

            # Initialize episodic memory
            self.episodic_memory = EpisodicMemory(self.db_pool)
         
            # Compile graph only after checkpointer is ready
            self.graph = self.agent_executor.graph.compile(self.checkpointer)

            log.info("MCP, Postgres checkpointer and episodic memory DB started")

        except Exception:
            log.exception("Error occured while initialize_mcp_checkpointer")
            raise
    


    async def get_payload_data(self,user_name,thread_id,question):
        try:
            user_name = validate_user_id(user_name)
            result = await self.initialize_langgraph(user_name,thread_id,question)
            return result
        except Exception:
            raise


    async def initialize_langgraph(self,user_name,thread_id,question):
        try:

            execution_id = str(uuid4())
            self.llm_open_ai = llm_call().port_key(user_name, execution_id)
            runtime_context = RuntimeContextSchema(user_id = user_name, 
                                                   checkpointer =  self.checkpointer , 
                                                   backend = self.agent_executor.store_backend,  
                                                   episodic_memory = self.episodic_memory,
                                                   llm_open_ai = self.llm_open_ai
                                                  )
            
            log.info("Execution_id: %s",execution_id)
            config = {
                        "configurable" : {"thread_id": thread_id},   
                        "metadata": {"user_id": user_name, "execution_id" : execution_id}
                     }

    
    
            log.info("QUESTION RECEIVED BY API: %s", question)
            log.info("========== BEFORE GRAPH AINVOKE ==========")

            result = await self.graph.ainvoke( {
                
                                                 "user_request": question, 
                                                 "messages" :[HumanMessage(content = question)]
                                                },
                                                  config = config, 
                                                  context = runtime_context
                                              )

            if "__interrupt__" in result:

                log.info("GRAPH INTERRUPT CAUGHT IN DEEP_AGENT_EXECUTOR:thread_id = %s",thread_id)

                interrupt = result["__interrupt__"][0]

                return {
                            "status":"waiting_for_approval",
                            "thread_id": thread_id,
                            "action_requests":interrupt.value["action_requests"],
                            "review_configs": interrupt.value["review_configs"],
                            "execution_id" : execution_id,
                       }
            
            
            log.info("========== AFTER GRAPH AINVOKE ==========")

            log.info("Final_agnet_output:%s",result["final_answer"])
            
            return result
            
            
        except Exception:
            log.exception("Error while executing LangGraph")
            raise

    async def interrupt_resume(self,decisions,thread_id,user_name, execution_id):
        try:
            runtime_context = RuntimeContextSchema(user_id = user_name, 
                                                   checkpointer =  self.checkpointer , 
                                                   backend = self.agent_executor.store_backend, 
                                                   episodic_memory = self.episodic_memory,
                                                   llm_open_ai = self.llm_open_ai)
            
            config = {"configurable" : {"thread_id": thread_id},   "metadata": {"user_id": user_name, "execution_id" : execution_id}}

            log.info("RESUMING GRAPH: thread_id=%s decision=%s", thread_id, decisions)

            result = await self.graph.ainvoke(  
                                                Command(resume={
                                                        "decisions": decisions
                                                        } 
                                                    
                                                ),
                                                config = config,
                                                context = runtime_context
                                                )
            if "__interrupt__" in result:
                log.info("Another HITL interrupt occurred")
                interrupt = result["__interrupt__"][0]

                return {
                    "status": "waiting_for_approval",
                    "thread_id": thread_id,
                    "action_requests": interrupt.value["action_requests"],
                    "review_configs": interrupt.value["review_configs"],
                    "execution_id":execution_id,
                   }

            log.info("========== AFTER GRAPH AINVOKE_POST_Interrupt ==========")
            log.info("Final_agnet_output:%s",result["final_answer"])
            
            return result
           
        except Exception:
            log.exception("Error while resuming LangGraph")
            raise





    
   
