from app.executor.langgraph.graph import AgentExecutor
from app.schemas.custom_schemas import RuntimeContextSchema
from logger.log import setup_logging
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from config.database_config import DB_URI
log = setup_logging()

class ServiceLayer:
    def __init__(self):
        self.agent_executor = AgentExecutor()
        self.checkpointer = None

    async def initialize_mcp_checkpointer(self):
        try:
            await self.agent_executor.mcp_manager.start()

            # Start async Postgres checkpointer
            self.agent_executor.checkpointer_context = await self.agent_executor.exit_stack.enter_async_context(AsyncPostgresSaver.from_conn_string(DB_URI))   #as creating a recipe/instruction for a database connection, not necessarily opening the connection yet.
            #self.checkpointer = await self.checkpointer_context.__aenter__() # Open/initialize this resource and give me the actual checkpointer."
            await self.agent_executor.checkpointer_context.setup()
            
            # Compile graph only after checkpointer is ready
            self.graph = self.agent_executor.graph.compile(self.agent_executor.checkpointer_context)

            self.checkpointer  = self.agent_executor.checkpointer_context
            log.info("MCP and Postgress server started")
        except Exception:
            log.exception("Error occured while initialize_mcp_checkpointer")
            raise
    


    async def get_payload_data(self,user_name,thread_id,question):
        try:
            result = await self.initialize_langgraph(user_name,thread_id,question)
            return result
        except Exception:
            raise


    async def initialize_langgraph(self,user_name,thread_id,question):
        try:
            runtime_context = RuntimeContextSchema(user_id = user_name, checkpointer =  self.checkpointer , backend = self.agent_executor.store_backend)
            config = {"configurable" : {"thread_id": thread_id}}

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
                            "review_configs": interrupt.value["review_configs"]
                       }
            
            
            
            log.info("========== AFTER GRAPH AINVOKE ==========")
            log.info("Final_agnet_output:%s",result["final_answer"])
            
            return result
            
            
        except Exception:
            log.exception("Error while executing LangGraph")
            raise

    async def interrupt_resume(self,decision,thread_id,user_name):
        try:
            runtime_context = RuntimeContextSchema(user_id = user_name, checkpointer =  self.checkpointer , backend = self.agent_executor.store_backend)
            config = {"configurable" : {"thread_id": thread_id}}

            log.info("RESUMING GRAPH: thread_id=%s decision=%s", thread_id, decision)
            
            result = await self.graph.ainvoke(  
                                                Command(resume={
                                                        "decisions": [
                                                            {"type": decision} 
                                                        ]
                                                    }
                                                ),
                                                config = config,
                                                context = runtime_context
                                                )
            if "__interrupt__" in result:
                # Another HITL interrupt occurred
                log.info("Another HITL interrupt occurred")
                interrupt = result["__interrupt__"][0]

                return {
                    "status": "waiting_for_approval",
                    "thread_id": thread_id,
                    "action_requests": interrupt.value["action_requests"],
                    "review_configs": interrupt.value["review_configs"]
                   }

            log.info("========== AFTER GRAPH AINVOKE_POST_Interrupt ==========")
            log.info("Final_agnet_output:%s",result["final_answer"])
            
            return result
           
        except Exception:
            log.exception("Error while resuming LangGraph")
            raise





    
   
