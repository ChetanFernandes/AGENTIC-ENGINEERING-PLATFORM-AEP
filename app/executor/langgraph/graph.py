from app.schemas.custom_schemas import CustomState 
from app.schemas.agent_output_schema import AgentOutput, AgentExecutionResult
from langgraph.graph import StateGraph, START , END 
from app.executor.context_management.context_manager import ContextManager
from config.llm_config import llm_openai
from deepagents import create_deep_agent
from langsmith.sandbox import SandboxClient
from app.executor.langgraph.prompt_1 import main_agent_system_prompt
from app.middleware.tool_call_tracking_middleware.tool_tracking import state_Tool_Tracking
from app.middleware.summarization_middleware.summarization_middleware import create_summarization_middleware
from app.middleware.tool_retry_middleware.tool_retry import (
    tool_error_retry_middleware, model_error_middleware, model_call_limit_middleware,tool_call_limit_middleware)
from app.middleware.context_editing_middleware.context_editing import context_editing_middleware
from app.sub_agent.sub_agents_1 import sub_agent_caller
from deepagents.backends import CompositeBackend, LangSmithSandbox
from consolidation_agent.consolidation_agent import search_recent_conversation
from deepagents import FilesystemPermission
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig
from app.backends.store.store import backend
from app.artifacts_storage.azure_blob import BlobStorage
from app.mcp.mcp_manager.mcp_manager import MCPManager
from langchain.agents.middleware import HumanInTheLoopMiddleware
from app.utilis.utilis import client_factories, client_group, is_broken_mcp_session, InterruptDefinition,normalize_agent_output
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
from pprint import pformat
from pprint import pprint
#from langgraph.checkpoint.memory import MemorySaver
from dataclasses import dataclass
from logger.log import setup_logging
log = setup_logging()


@dataclass
class ContextSchema():
    user_id:str

class AgentExecutor:

    try:
    
        def __init__(self):
            self.graph = StateGraph(CustomState)
            self.context_manager = ContextManager()

            # MCP
            self.mcp_manager = MCPManager(client_group=client_group, client_factories=client_factories, pool_size=5)

            # Sandbox
            self.client = SandboxClient()
            #sandbox = self.client.list_sandboxes()
            self.ls_sandbox = self.client.create_sandbox()
            '''
            existing = next((sandbox for sandbox in sandboxes if sandbox.name =="aep-sandbox"),None)
            if existing:
                self.ls_sandbox = existing
                log.info("Reusing Sandbox:%s ->", self.ls_sandbox.name)
            else:
                self.ls_sandbox = self.client.create_sandbox(name="aep-sandbox")
                log.info("Created sandbox -> %s", self.ls_sandbox.name)
            '''  
            self.sandbox_backend = LangSmithSandbox(sandbox = self.ls_sandbox)
    

            # adding nodes
            self.graph.add_node("router",self.router)
            self.graph.add_node("orchestrator",self.orchestrator)
            self.graph.add_node("details_gathering_node", self.details_gathering_node)
            self.graph.add_node("deep_agent_executor", self.deep_agent_executor)
            self.graph.add_node("state_tracking_before_deep_agent_execution",self.state_tracking_before_deep_agent_execution)
            self.graph.add_node("state_tracking_after_deep_agent_execution",self.state_tracking_after_deep_agent_execution)
            self.graph.add_node("store_tracking_after_deep_agent_execution",self.store_tracking_after_deep_agent_execution)
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
            self.graph.add_edge("state_tracking_after_deep_agent_execution","store_tracking_after_deep_agent_execution")
            self.graph.add_edge("store_tracking_after_deep_agent_execution","orchestrator")
            self.graph.add_edge("end_node", END)


            #self.checkpointer = MemorySaver()

            self.checkpointer_context = None
            self.store_backend = backend(blob_storage = BlobStorage())
            self.distructive_tools = None
            self.interrupt_on = {}
            self.discarded = False
            self.exit_stack = AsyncExitStack()

    except Exception:
        log.exception("Error while initializing graph")
        raise


    def format_previous_question(self,messages,current_question):
        requests = []
        for message in messages:
            if isinstance(message, HumanMessage):
                if message.content != current_question:
                    requests.append(message.content)

        return "\n\n".join(f"previous_requests: {i+1}: {message}" for i, message in enumerate(requests))

    async def router(self, state:CustomState , runtime:Runtime, config : RunnableConfig ):
        try:

            log.info("user_id:%s",runtime.context.user_id)
            log.info("checkpointer:%s",runtime.context.checkpointer)
            log.info("backend:%s",runtime.context.backend)
            log.info("thread_id:%s",config["configurable"].get("thread_id","NA"))
            
            current_question = state["user_request"]
            previous_question = state.get("messages", [])

            previous_questions = self.format_previous_question(previous_question,current_question)

            chat_template = ChatPromptTemplate.from_messages([
                                                        ("system", ROUTER_SYSTEM_PROMPT), 
                                                        ("human", """
                                                                    Conversation history : {previous_questions}

                                                                    Current user request: {user_request}
                                                                    
                                                                 """
                                                        )
                                                    ])
            structured_llm = llm_openai.with_structured_output(RouteDecision)

            router_chain = chat_template | structured_llm

            routing_information = await router_chain.ainvoke({"previous_questions": previous_questions, "user_request": question})
        
            return {
                            "routing_information": routing_information,
                            "artifacts_id": {"__reset__": "__RESET__"},
                            "successful_route_executed": {"__reset__": "__RESET__"},
                            "failed_route_executed": {"__reset__": "__RESET__"},
                            "context_given_agent": {},
                            "ready_routes": [],
                            "final_answer": None,
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
       

    async def details_gathering_node(self,state:CustomState, runtime:Runtime):
        try:
            ready_agents = state["ready_routes"]

            log.info("Details gathering for ready agent:%s", ready_agents)

            user_id = runtime.context.user_id

            async def build_route_context(route):
                agent_name = route["agent"]
                task = route["task"]

                result = await self.context_manager.build_context(agent_name, task, user_id, self.store_backend, state)

                return agent_name, result.context

            results = await asyncio.gather(
                                            *(build_route_context(route) for route in ready_agents)
                                        )

            # asyncio.gather() collects all those returned values into a list.

            for agent_name , result in results:

                log.info("Details gathered for :%s , :%s", agent_name , result)

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

            log.info("Agent -> %s", state.get("agent", "NA"))
            log.info("Route_id -> %s", state.get("route_id", "NA"))
            log.info("Task -> %s", state.get("task", "NA"))

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
                                "context_given_agent": state.get("context_given_agent",{})
                            
                            }
                        )
                            
                for route in ready_routes 
                ]
        except Exception:
            log.exception("Error occured during execution of fan_out_routes_node")
            raise
            
    
    async def deep_agent_executor(self,state:CustomState, runtime:Runtime, config : RunnableConfig):
        try:

            current_route = state["current_route"]

            task = current_route["task"]
            agent_name = current_route["agent"]
            route_id = current_route["route_id"]
            route_is_final = current_route.get("is_final", False)

            content = state["context_given_agent"].get(agent_name,{})
            user_question = state.get("user_request")


            log.info("Deep_agent_is_executing_agent -> %s", agent_name)
            log.info("Task for agent is->%s",task)
            log.info("Route_id->%s",route_id)
            log.info("Context given is -> %s",content)

            
            user_id = runtime.context.user_id

            user_memory_file = f"/memories/personal/{user_id}_USER_MEMORY.md"
            #user_memory_file=user_memory_file
            system_prompt = main_agent_system_prompt                          
            session_entry = await self.mcp_manager.acquire("github_1")
            mcp_tools = session_entry.tools
            searchable_tools = [tool.name for tool in mcp_tools]
            interrupt = InterruptDefinition(session_entry.tools)


            if self.distructive_tools is None:
                self.distructive_tools = interrupt.save_distructive_tools()
                log.info("Calling self distructive function once ->%s",  self.distructive_tools)

            else:
                log.info("For second round self distructibe tools not called ->%s",self.distructive_tools)


            if not self.interrupt_on:
                self.interrupt_on = interrupt.define_interrupt_on()
                log.info("Calling interrupt function once ->%s",self.interrupt_on)
            else:
                log.info("For second round self interrput not called -> %s",self.interrupt_on )
            

            memory_wrapper, skills_wrapper = self.store_backend.policy_wrapper()
        

        
            deep_agent = create_deep_agent(model = llm_openai, 
                                           backend = CompositeBackend(
                                                                        default = self.sandbox_backend, 

                                                                        routes = 
                                                                                {         
                                                                                    "/memories/shared/": memory_wrapper,
                                                                                    "/memories/personal/": self.store_backend.store_backend_memory_personal(), 
                                                                                    "/skills/repository-analysis/": skills_wrapper, 
                                                                                }
                                                                     ),

                                            
                                            system_prompt = system_prompt, 
                                            response_format=AgentOutput, 
                                            middleware=[state_Tool_Tracking(store = self.store_backend.return_store(), backend = self.store_backend), 
                                                                            *tool_error_retry_middleware(),
                                                                            model_error_middleware(),
                                                                            create_summarization_middleware(self.sandbox_backend),
                                                                            model_call_limit_middleware(),
                                                                            tool_call_limit_middleware(),
                                                                            context_editing_middleware(),
                                                                            #ProviderToolSearchMiddleware(searchable_tools = searchable_tools),
                                                                            HumanInTheLoopMiddleware(interrupt_on = self.interrupt_on)], 
                                            subagents = [sub_agent_caller()],
                                            store = self.store_backend.return_store() ,
                                            checkpointer = self.checkpointer_context ,
                                            tools = mcp_tools + [search_recent_conversation],
                                            permissions = [ FilesystemPermission(operations=['read','write'], paths=["/memories/personal/", "/memories/shared/LEARNINGS.md"], mode = 'allow'),],
                                            memory = ["/memories/shared/LEARNINGS.md", "/memories/shared/AGENTS.md" , user_memory_file])
                                                    
  
            result = await deep_agent.ainvoke(
                                                {
                                                    "messages" :[ 
                                                                    {
                                                                        "role": "user",
                                                                        "content": (    f"Human_question:\n{user_question}\n"
                                                                                        f"Task:\n{task}\n\n"
                                                                                        f"Relevant Context from Previous Agents:\n{content}\n\n"
                                                                                    )
                                                                    }
                                                                ]
                                                },

                                                config = config,
                                                context = runtime.context)

            log.info("Result type:%s", type(result))

            log.info("Result keys:%s", result.keys())

            agent_output = normalize_agent_output(result)

            log.info("Agent_ouptut:%s", agent_output)

            status = agent_output.status.lower()

            artifact_record = self.store_backend.store_agent_output(agent_name, user_id, agent_output )

            if route_is_final and status == "success":
                
                return {"artifacts_id" : {agent_name : artifact_record.artifact_id}, "successful_route_executed" : {route_id: agent_name}, "final_answer": agent_output}

            elif route_is_final and status in ("partial_success", "failed"):

                return {"artifacts_id" : {agent_name : artifact_record.artifact_id}, "failed_route_executed" : {route_id: agent_name}, "final_answer": agent_output}

            elif status == "success":
                 
                return {"artifacts_id": {agent_name: artifact_record.artifact_id}, "successful_route_executed": {route_id: agent_name}}

            else:

                return {"artifacts_id" : {agent_name : artifact_record.artifact_id}, "failed_route_executed" : {route_id: agent_name}}
            
        except GraphInterrupt:
            raise
           
        except Exception as exc:

            log.exception("Error occured during execution of node deep_agent_executor")

            if is_broken_mcp_session(exc):

                await self.mcp_manager.discard_and_replace("github_1", session_entry)

                self.discarded = True

            else:
                raise
        '''
        finally:

            if self.ls_sandbox:
                #self.client.delete_sandbox(self.ls_sandbox.name)

            if not self.discarded:
                await self.mcp_manager.release("github_1", session_entry)
        '''

    def fan_in_routes(self, state: CustomState):
        try:
            log.info("Parallel route execution completed. Successful=%s Failed=%s",
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

            ready_route = state["ready_routes"]

            log.info("State_Tracking_post_execution_of_ready_agents")

            if state:

                log.info("user_message_history -> %s", state.get("message", "NA"))
                
                log.info("ready_routes -> %s", state.get("ready_routes", "NA"))

                log.info("successful_route_executed -> %s",state.get("successful_route_executed", "NA"))

                log.info("failed_route_executed -> %s",state.get("failed_route_executed", "NA"))

                log.info("artifacts_id -> %s", state.get("artifacts_id", "NA"))

                log.info("context_given_agent ->%s ",state.get("context_given_agent", "NA"))

                log.info("routing_information ->%s ",state.get("routing_information", "NA"))

                log.info("user_request -> %s", state.get("user_request", "NA"))

        except Exception:
            log.exception("Error occured during execution of node state_tracking_after_deep_agent_execution")
            raise

    def store_tracking_after_deep_agent_execution(self, state:CustomState, runtime:Runtime):

        try:

            log.info('Store_contents_post_ready_agent_execution:%s',state["ready_routes"])

            user_id = runtime.context.user_id
        
            log.info("New_learning_updated in store:%s", self.store_backend.read_agent_learning())
    
            log.info("User_memory_updated ->%s", self.store_backend.read_user_personal_memory(user_id))

        except Exception:
            log.exception("Error occured during execution of node store_tracking_after_deep_agent_execution")
            raise
        
        
    async def end_node(self,state:CustomState):
        try:
            log.info("Workflow completed. Closing MCP manager.")
            #await self.mcp_manager.close()
            return {}
        except Exception:
            log.exception("Error occured during execution of end_node")
            raise
        





    













''' 


coordinator_messages : list[str] = []
subagent_handler = []

for name, item in result.interleave("messages","subagents"):
    if name == "message":
        print("[corrdiantor]", item.text)
        coordinator_messages.append(item.text)
    else:
        print(f"[{item.name}] started")
        subagent_handler.append(item)
        for message in item.messages:
            print(f"[{item.name}]", message.text)
        print(f"[{item.name}] status: {item.status}")


log.info("Deep agent raw result: %s", pformat(result))
         
LangGraph Node
      ↓
get_agent(agent_name)
      ↓
agent.execute(task)
      ↓
AgentOutput
      ↓
return state update

State = small information needed to run the workflow.
Artifact Store = detailed information we want to keep.
Context = temporary information we give an agent to do its job.
'''

'''
deep_agent_executor()
        │
        ▼
   MCP Manager
        │
        ├── MCP Server 1
        ├── MCP Server 2
        ├── MCP Server 3
        │
        ├── connection management
        ├── connection pooling
        ├── tool discovery
        ├── tool caching
        └── protocol/version handling
        │
        ▼
    MCP Tools
        │
        ▼
create_deep_agent(... tools = MCP tools ...)
'''