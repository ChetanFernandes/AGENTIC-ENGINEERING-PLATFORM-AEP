from app.schemas.custom_schemas import CustomState 
from app.schemas.agent_output_schema import AgentOutput
from langgraph.graph import StateGraph, START , END 
from app.executor.context_management.context_manager import ContextManager
from config.llm_config import llm_call
from deepagents import create_deep_agent
from langsmith.sandbox import SandboxClient  
from app.executor.langgraph.prompt_1 import main_agent_system_prompt
from app.middleware.tool_call_tracking_middleware.tool_tracking import state_Tool_Tracking
from app.middleware.summarization_middleware.summarization_middleware import create_summarization_middleware
from app.middleware.tool_retry_middleware.tool_retry import (
    tool_error_retry_middleware, model_error_middleware, model_call_limit_middleware, tool_call_limit_middleware)
from app.middleware.context_editing_middleware.context_editing import context_editing_middleware
from app.sub_agent.sub_agents_1 import sub_agent_caller
from deepagents.backends import CompositeBackend
from consolidation_agent.consolidation_agent_1 import search_recent_conversation
from deepagents import FilesystemPermission
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig
from app.backends.store.store import backend
from app.artifacts_storage.azure_blob import BlobStorage
from app.mcp.mcp_manager.mcp_manager import MCPManager
from langchain.agents.middleware import HumanInTheLoopMiddleware
from app.utilis.utilis import is_broken_mcp_session, normalize_agent_output, format_previous_question, sandbox_provision
from app.utilis.interrupt_utilis import InterruptDefinition
from langgraph.errors import GraphInterrupt
from langchain.agents.middleware import ProviderToolSearchMiddleware
from langchain_core.prompts import ChatPromptTemplate
from app.router.prompts import ROUTER_SYSTEM_PROMPT
from app.router.schemas import RouteDecision
from app.orchestration.orchestrator import RouteOrchestor
from contextlib import AsyncExitStack
from langgraph.types import Send
import asyncio
from langchain_core.messages import HumanMessage
from app.memory.episodic_memory import EpisodicMemory
from pprint import pformat
from pprint import pprint
#from langgraph.checkpoint.memory import MemorySaver
from dataclasses import dataclass
from logger.log import setup_logging
log = setup_logging()

'''
@dataclass
class ContextSchema():
    user_id:str
''' 

class AgentExecutor:

    try:
    
        def __init__(self):
            self.graph = StateGraph(CustomState)
            self.context_manager = ContextManager()
            self.llm_factory = llm_call()

            # MCP
            self.mcp_manager = MCPManager(pool_size=5)

            # Sandbox
            self.client = SandboxClient()
        
            # adding nodes
            self.graph.add_node("router",self.router)
            self.graph.add_node("orchestrator",self.orchestrator)
            self.graph.add_node("details_gathering_node", self.details_gathering_node)
            self.graph.add_node("deep_agent_executor", self.deep_agent_executor)
            self.graph.add_node("state_tracking_before_deep_agent_execution",self.state_tracking_before_deep_agent_execution)
            self.graph.add_node("state_tracking_after_deep_agent_execution",self.state_tracking_after_deep_agent_execution)
            self.graph.add_node("fan_in_routes", self.fan_in_routes)
            self.graph.add_node("end_node", self.end_node)

            # self.graph.set_entry_point("general_node")
            # set_entry_point(node) defines the first node the graph will execute. It is equivalent to builder.add_edge(START, node).
            # set_finish_point(node) defines the last node in the graph. It is equivalent to builder.add_edge(node, END).
            # Both methods are valid but add_edge(START, ...) and add_edge(..., END) are the recommended modern syntax.

            self.graph.add_edge(START, "router")
            self.graph.add_edge("router", "orchestrator")
            self.graph.add_conditional_edges("orchestrator", self.route_after_orchestrator, {"revert_to_details_gathering_node": "details_gathering_node", "end_node": "end_node"})
            self.graph.add_edge("details_gathering_node","state_tracking_before_deep_agent_execution")
            self.graph.add_conditional_edges("state_tracking_before_deep_agent_execution",self.fan_out_routes)
            self.graph.add_edge("deep_agent_executor","fan_in_routes")
            self.graph.add_edge("fan_in_routes","state_tracking_after_deep_agent_execution")
            self.graph.add_edge("state_tracking_after_deep_agent_execution","orchestrator")
            self.graph.add_edge("end_node", END)


            #self.checkpointer = MemorySaver()

            self.distructive_tools = None
            self.interrupt_on = {}
            self.discarded = False
            self.exit_stack = AsyncExitStack()
            self.sandbox_backend = None
            self.ls_sandbox = None

        async def initialize(self):
            self.store_backend = await backend.create(blob_storage=BlobStorage())  # Python automatically passes the backend class as cls.

    except Exception:
        log.exception("Error while initializing graph")
        raise


    async def router(self, state:CustomState , runtime:Runtime, config : RunnableConfig ):
        try:
            self.sandbox_backend, self.ls_sandbox = await asyncio.to_thread(sandbox_provision,self.client)
            log.info("user_id:%s",runtime.context.user_id)
            #log.info("llm_open_ai:%s",runtime.context.llm_open_ai)
            log.info("thread_id:%s",config["configurable"].get("thread_id","NA"))
            
            current_question = state["user_request"].strip()

            log.info("user_request:%s",current_question)

            previous_question_history = state.get("messages", [])

            previous_accumulated_questions = []

            if previous_question_history:
                for message in previous_question_history:
                    if isinstance(message, HumanMessage):
                        content = message.content.strip()
                        if content != current_question:
                            previous_accumulated_questions.append(content)

            log.info("previous_accumulated_questions:\n %s",previous_accumulated_questions)
            log.info("Length of previous questions:%s", len(previous_accumulated_questions))

            formatted_questions = ""

            if previous_accumulated_questions:
                formatted_questions = format_previous_question(previous_accumulated_questions, current_question)
                log.info("Formatted_question:\n%s",formatted_questions)

            chat_template = ChatPromptTemplate.from_messages([
                                                        ("system", ROUTER_SYSTEM_PROMPT), 
                                                        ("human", """
                                                                    Conversation history : {previous_questions}

                                                                    Current user request: {user_request}
                                                                    
                                                                 """
                                                        )
                                                    ])
            


            llm_openai =  runtime.context.llm_open_ai
            
            structured_llm = llm_openai.with_structured_output(RouteDecision)

            router_chain = chat_template | structured_llm

            routing_information = await router_chain.ainvoke({"previous_questions": formatted_questions, "user_request": current_question})
        
            return {
                            "routing_information": routing_information,
                            "artifacts_id": {"__reset__": "__RESET__"},
                            "successful_route_executed": {"__reset__": "__RESET__"},
                            "failed_route_executed": {"__reset__": "__RESET__"},
                            "context_given_agent": {},
                            "ready_routes": [],
                            "final_answer": None,
                            "user_request": current_question
                    }
        
        except Exception:
            log.exception("Error occured duing execution of node router")

    async def orchestrator(self,state:CustomState):
        try:
            route_orchestrator = RouteOrchestor()
            return await route_orchestrator.execution_director(state)
        except Exception:
            log.exception("Error occured during execution of node orchestrator")
            raise
       

    async def details_gathering_node(self,state:CustomState, runtime:Runtime,):
        try:
            ready_agents = state["ready_routes"]

            log.info("Agent ready for execution:\n%s", ready_agents)

            user_id = runtime.context.user_id

            async def build_route_context(route):
                agent_name = route["agent"]
                task = route["task"]

                result = await self.context_manager.build_context(agent_name, task, user_id, self.store_backend, state, runtime.context.llm_open_ai)

                return agent_name, result.context

            results = await asyncio.gather(
                                            *(build_route_context(route) for route in ready_agents)
                                        )

            # asyncio.gather() collects all those returned values into a list.

            #for agent_name , result in results:

                #log.info("Details gathered for :%s , :%s", agent_name , result)

            context_given_agent = dict(results)

            log.info("Context gathered for agents -> %s", context_given_agent)

            return {"context_given_agent" : context_given_agent}
        except Exception:
            log.exception("Error occured during execution of details_gathering_node ")
            raise



    def state_tracking_before_deep_agent_execution(self,state:CustomState):
        try:
            log.info('state_tracking_ready_agents_to execution')
    
            log.info("Ready Routes -> %s", state.get("ready_routes", []))
            log.info("Context_given_agent ->%s ", state.get("context_given_agent", {}))

            return {}
        except Exception:
            log.exception("Error occured during execution of state_tracking_before_deep_agent_execution_node")
            raise


    def fan_out_routes(self,state:CustomState):
        try:
            ready_routes = state["ready_routes"]
            log.info("ready_routes -> %s", ready_routes)
            return [
                    Send(
                            "deep_agent_executor",

                            {  
                                "current_route": route,
                                "context_given_agent": state.get("context_given_agent",{}),
                                "user_question" : state.get("user_request")
                            
                            }
                        )
                            
                for route in ready_routes 
                ]
        except Exception:
            log.exception("Error occured during execution of fan_out_routes_node")
            raise
            
    
    async def deep_agent_executor(self,state:CustomState, runtime:Runtime, config : RunnableConfig):
        session_entry = None
        try:
            current_route = state["current_route"]
            task = current_route["task"]
            agent_name = current_route["agent"]
            route_id = current_route["route_id"]
            route_is_final = current_route.get("is_final", False)
            content = state["context_given_agent"].get(agent_name,{})
            user_question = state.get("user_question")

            log.info("Deep_agent_is_executing_agent -> %s", agent_name)
            log.info("Task for agent is->\n%s",task)
            log.info("Route_id->%s",route_id)
            log.info("Context given is -> %s",content)
  
            user_id = runtime.context.user_id
            user_memory_file = f"/user_memories/USER_MEMORY.md"
            system_prompt = main_agent_system_prompt.replace("{user_memory_file}", user_memory_file)                     
            session_entry = await self.mcp_manager.acquire("github")
            mcp_tools = session_entry.tools
            #searchable_tools = [tool.name for tool in mcp_tools]
            interrupt = InterruptDefinition(session_entry.tools)


            if self.distructive_tools is None:
                self.distructive_tools = interrupt.save_distructive_tools()
                log.info("Calling self distructive function once ->\n%s",  self.distructive_tools)
            else:
                log.info("For second round self distructibe tools not called ->\n%s",self.distructive_tools)


            if not self.interrupt_on:
                self.interrupt_on = interrupt.define_interrupt_on()
                log.info("Calling interrupt function once ->\n%s",self.interrupt_on)
            else:
                log.info("For second round self interrput not called -> \n%s",self.interrupt_on )
            

            main_agent_memory_wrapper, main_agent_learning_wrapper, subagent_skills_wrapper = self.store_backend.policy_wrapper()
    
            llm_open_ai = runtime.context.llm_open_ai
            deep_agent = create_deep_agent(

                    model = llm_open_ai, 
                    backend = CompositeBackend
                                (
                                    default = self.sandbox_backend, 
                                    routes = 
                                            {         
                                                "/main_agent_skill/": main_agent_memory_wrapper,
                                                "/main_agent_learning/": main_agent_learning_wrapper,
                                                "/user_memories/": self.store_backend.store_backend_memory_personal(), 
                                                "/sub_agent_skills/": subagent_skills_wrapper, 
                                            }
                                ),

                    
                    system_prompt = system_prompt, 
                    response_format = AgentOutput, 
                    middleware = [    
                                    state_Tool_Tracking(store = self.store_backend.return_store(), backend = self.store_backend), 
                                    #create_summarization_middleware(self.sandbox_backend,llm_open_ai),
                                    context_editing_middleware(),
                                    HumanInTheLoopMiddleware(interrupt_on = self.interrupt_on),
                                    #ProviderToolSearchMiddleware(searchable_tools = searchable_tools)
                                 ], 
                      
                                                    
                    subagents = [sub_agent_caller(llm_open_ai)],
                    store = self.store_backend.return_store() ,
                    checkpointer = runtime.context.checkpointer ,
                    tools = mcp_tools + [search_recent_conversation, self.store_backend.get_write_memory_tool()],
                    permissions = [FilesystemPermission(operations=['read','write'], paths=["/user_memories/", "/main_agent_learning/","/sub_agent_skills/"], mode = 'allow'),],
                    memory = ["/main_agent_skill/AGENTS.md"],
    
                                            )
                                                    

            result = await deep_agent.ainvoke(
                                                {
                                                    "messages" :[ 
                                                                    {
                                                                        "role": "user",
                                                                        "content": (  
                                                                                        f"Task:\n{task}\n\n"
                                                                                        f"Relevant Context from Previous Agents:\n{content}\n\n"
                                                                                    )
                                                                    }
                                                                ]
                                                },

                                                config = config,
                                                context = runtime.context)
            messages = result.get("messages", [])
 
            log.info("========== DEEP AGENT RESPONSE ==========")
            log.info("MESSAGE COUNT: %d", len(messages))
            #log.info("Agent_output_before_episodic_memory%s",messages)

            episodic_memory = runtime.context.episodic_memory

            execution_id = config["metadata"]["execution_id"]

            thread_id = config["configurable"]["thread_id"]
            
            await episodic_memory.add_execution_history(execution_id=execution_id, messages = messages, user_request = user_question, thread_id=thread_id, user_id = user_id)

            '''
            for i, msg in enumerate(messages):
                log.info("MSG[%d] type=%s id=%s content_type=%s",
                    i,
                    type(msg).__name__,
                    getattr(msg, "id", None),
                    type(getattr(msg, "content", None)).__name__,
                )
            

                log.info("MSG[%d] content=%s", i, str(getattr(msg, "content", ""))[:100])
            '''

            structured_response = result.get("structured_response")

            log.info("STRUCTURED RESPONSE TYPE: %s", type(structured_response).__name__)

            log.info("Result keys:%s", result.keys())
            
            #log.info("Agent_output_before_normalizing:%s", structured_response)

            agent_output = normalize_agent_output(result)

            log.info("Agent_output_after_normalizing:%s", agent_output)

            status = agent_output.status.lower()

            execution_id = config["metadata"]["execution_id"]
            
            artifact_record = await self.store_backend.store_agent_output(agent_name, user_id, agent_output, execution_id )

            if route_is_final and status == "success":
                
                return {"artifacts_id" : {agent_name : artifact_record.artifact_id}, "successful_route_executed" : {route_id: agent_name}, "final_answer": agent_output}

            elif route_is_final and status in ("failed","partial_success","blocked",):

                return {"artifacts_id" : {agent_name : artifact_record.artifact_id}, "failed_route_executed" : {route_id: agent_name}, "final_answer": agent_output}

            elif status == "success":
                 
                return {"artifacts_id": {agent_name: artifact_record.artifact_id}, "successful_route_executed": {route_id: agent_name}}

            else:

                return {"artifacts_id" : {agent_name : artifact_record.artifact_id}, "failed_route_executed" : {route_id: agent_name}}
            
        except GraphInterrupt:
            raise
           
        except Exception as exc:

            log.exception("Error occured during execution of node deep_agent_executor")

            if (session_entry is not None and is_broken_mcp_session(exc)):
                log.warning("Broken MCP session detected | "
                            "server=%s",
                            session_entry.server_name
                            )

                await self.mcp_manager.discard_and_replace(session_entry)

                self.discarded = True
                # Important:
                # This session has already been discarded.
                #
                # Therefore finally must NOT release it.
                session_entry = None

            raise

        finally:
            # =====================================================
            # Always return healthy acquired session
            # 
            if session_entry is not None:
                log.info(
                "Releasing MCP session | server=%s",
                session_entry.server_name
            )
                await self.mcp_manager.release(session_entry)
    

    def fan_in_routes(self, state: CustomState):
        try:
            log.info("Parallel route execution completed. \nSuccessful=\n%s \nFailed=\n%s",
                    state.get("successful_route_executed", {}),
                    state.get("failed_route_executed", {})
                )

            return {}
        except Exception:
            log.exception("Error occured during execution of node fan_in_routes")
            raise

    def route_after_orchestrator(self, state: CustomState):
        try:
            if state.get("ready_routes"):
                return "revert_to_details_gathering_node"

            return "end_node"
        except Exception:
            log.exception("Error occured during execution of node route_after_orchestrator")
            raise

     
    def state_tracking_after_deep_agent_execution(self, state: CustomState):
        try:

            log.info("State_Tracking_post_execution_of_ready_agents")

            if state:

                log.info("user_message_history -> %s", state.get("messages", "NA"))

                log.info("Current user_request -> %s", state.get("user_request", "NA"))
                
                log.info("ready_routes -> %s", state.get("ready_routes", "NA"))

                log.info("successful_route_executed -> %s",state.get("successful_route_executed", "NA"))

                log.info("failed_route_executed -> %s",state.get("failed_route_executed", "NA"))

                log.info("artifacts_id -> %s", state.get("artifacts_id", "NA"))

                log.info("context_given_agent ->%s ",state.get("context_given_agent", "NA"))

                log.info("routing_information ->%s ",state.get("routing_information", "NA"))

                log.info("final_answer -> %s", state.get("final_answer", "NA"))

        except Exception:
            log.exception("Error occured during execution of node state_tracking_after_deep_agent_execution")
            raise



    async def end_node(self, state: CustomState, config: RunnableConfig, runtime: Runtime):
        try:
            execution_id = config["metadata"]["execution_id"]
            episodic_memory = runtime.context.episodic_memory
            user_id = runtime.context.user_id

            execution_data = episodic_memory.get_execution_history(execution_id)

            if execution_data:
                execution_data = await episodic_memory.recover_execution_history(execution_id)
                log.info(
                    "Execution history extracted for execution_id=\n%s, "
                    "agent_histories=\n%d",
                    execution_id,
                    len(execution_data.get("messages", []))
                )

                try:
                    await episodic_memory.store_execution(execution_data, user_id)

                    # Delete temporary PostgreSQL history only after successful storage
                    await episodic_memory.delete_in_progress_history(execution_id)

                    # Remove temporary in-memory execution history
                    episodic_memory.execution_histories.pop(execution_id, None)

                    log.info("Episodic memory stored successfully for execution_id=%s",execution_id)

                except Exception:
                    log.exception("Failed to store episodic memory for execution_id=%s. " "Continuing workflow.", execution_id)
            else:
                log.warning("No execution history found for execution_id=%s",execution_id)
  
            if self.ls_sandbox:
                log.info("Workflow completed. Deleting Sandbox:%s", self.ls_sandbox.name)
                self.client.delete_sandbox(self.ls_sandbox.name)

            return state

        except Exception:
            log.exception("Error occurred during execution of end_node")
            raise











