from app.schemas.custom_schemas import CustomState
from app.schemas.agent_output_schema import AgentOutput
from langgraph.graph import StateGraph, START , END 
from app.executor.context_management.context_manager import ContextManager
from config.llm_config import llm_openai
from deepagents import create_deep_agent
from langsmith.sandbox import SandboxClient
from pprint import pformat
from app.executor.langgraph.prompt import main_agent_system_prompt
from app.middleware.tool_call_tracking_middleware.tool_tracking import state_Tool_Tracking

from app.middleware.summarization_middleware.summarization_middleware import create_summarization_middleware
from app.middleware.tool_retry_middleware.tool_retry import (
    tool_error_retry_middleware, model_error_middleware, model_call_limit_middleware,tool_call_limit_middleware)
from app.middleware.context_editing_middleware.context_editing import context_editing_middleware
from app.sub_agent.sub_agents import sub_agent_caller
from deepagents.backends import CompositeBackend, LangSmithSandbox
#from langgraph.checkpoint.memory import MemorySaver
from consolidation_agent.consolidation_agent import search_recent_conversation
from deepagents import FilesystemPermission
from dataclasses import dataclass
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig
from app.backends.store.store import backend
from config.database_config import DB_URI
from pprint import pprint
from app.artifacts_storage.azure_blob import BlobStorage
from app.mcp.mcp_manager.mcp_manager import MCPManager
from app.utilis.utilis import InterruptDefinition
from langchain.agents.middleware import HumanInTheLoopMiddleware
from logger.log import setup_logging
log = setup_logging()
from app.utilis.utilis import client_factories, client_group, is_broken_mcp_session, InterruptDefinition
from langgraph.errors import GraphInterrupt
from langchain.agents.middleware import ProviderToolSearchMiddleware
from langchain_core.prompts import ChatPromptTemplate
from app.router.prompts import ROUTER_SYSTEM_PROMPT
from app.router.schemas import RouteDecision
from app.orchestration.orchestrator import RouteOrchestor
from contextlib import AsyncExitStack
from langgraph.types import Send
import asyncio

@dataclass
class ContextSchema():
    user_id:str

class AgentExecutor:
    
    def __init__(self):
        self.graph = StateGraph(CustomState)
        self.context_manager = ContextManager()

        # MCP
        self.mcp_manager = MCPManager(client_group=client_group, client_factories=client_factories, pool_size=5)

        # Sandbox
        self.client = SandboxClient()
        self.ls_sandbox = self.client.create_sandbox()
        self.sandbox_backend = LangSmithSandbox(sandbox = self.ls_sandbox)

        # adding nodes
        self.graph.add_node("router",self.router)
        self.graph.add_node("orchestrator",self.orchestrator)
        self.graph.add_node("details_gathering_node", self.details_gathering_node)
        self.graph.add_node("deep_agent_executor", self.deep_agent_executor)
        self.graph.add_node("state_tracking_before_deep_agent_execution",self.state_tracking_before_deep_agent_execution)
        self.graph.add_node("state_tracking_after_deep_agent_execution",self.state_tracking_after_deep_agent_execution)
        self.graph.add_node("store_tracking_after_deep_agent_execution",self.store_tracking_after_deep_agent_execution)
        self.graph.add_node("fan_out_routes", self.fan_out_routes)
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
        self.graph.add_edge("state_tracking_before_deep_agent_execution","fan_out_routes")
        self.graph.add_edge("deep_agent_executor","fan_in_routes")
        self.graph.add_edge("fan_in_routes","state_tracking_after_deep_agent_execution")
        self.graph.add_conditional_edges("state_tracking_before_deep_agent_execution",self.fan_out_routes)
        self.graph.add_edge("store_tracking_after_deep_agent_execution","orchestrator")
        self.graph.add_edge("end_node", END)


        #self.checkpointer = MemorySaver()

        self.checkpointer_context = None
        self.store_backend = backend(blob_storage = BlobStorage())
        self.distructive_tools = None
        self.interrupt_on = {}
        self.discarded = False
        self.exit_stack = AsyncExitStack()

    async def router(self, question, runtime:Runtime, config : RunnableConfig):
        #log.info("user_id:%s",runtime.context.user_name)
        log.info("checkpointer:%s",runtime.context.checkpointer)
        log.info("backend:%s",runtime.context.backend)
        #log.info("thread_id:%s",config["configurable"].get("thread_id","NA"))
 
        chat_template = ChatPromptTemplate.from_messages([
                                                    ("system", ROUTER_SYSTEM_PROMPT), 
                                                    ("human", "{user_request}")
                                                ])
        structured_llm = llm_openai.with_structured_output(RouteDecision)

        router_chain = chat_template | structured_llm

        routing_information = await router_chain.ainvoke({"user_request":question})
    
        return {"routing_information" : routing_information}

    async def orchestrator(self,state:CustomState):
        route_orchestrator = RouteOrchestor()
        return await route_orchestrator.execution_director(state)
       

    async def details_gathering_node(self,state:CustomState, runtime:Runtime):
        ready_agents = state["ready_routes"]

        log.info("Details gathering for ready agent:%s", ready_agents)

        user_id = runtime.context.user_name

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

            log.info("Details gathered for :%s , :%s", (agent_name , result))

        context_given_agent = dict(results)

        log.info("Context gathered for agents -> %s", context_given_agent)

        return {"context_given_agent" : context_given_agent}



    def state_tracking_before_deep_agent_execution(self,state:CustomState):
        log.info('state_tracking_ready_agents_to execution')
   
        log.info("Ready Routes -> %s", state.get("ready_routes", []))
        log.info("Context_given_agent ->%s ", state.get("context_given_agent", {}))

        log.info("Agent -> %s", state.get("agent", "NA"))
        log.info("Route_id -> %s", state.get("route_id", "NA"))
        log.info("Task -> %s", state.get("task", "NA"))

        return {}


    def fan_out_routes(self,state:CustomState):
        ready_routes = state["ready_routes"]
        return [
                Send(
                        "deep_agent_executor",
                        {"current_route": route}
                    )
                         
                for route in ready_routes
            ]
         
    
    async def deep_agent_executor(self,state:CustomState, runtime:Runtime, config : RunnableConfig):
        current_route = state["current_route"]
        log.info("Current_route",current_route)
        
        task = current_route["task"]
        agent_name = current_route["agent"]
        route_id = current_route["route_id"]
        content = state["context_given_agent"].get(agent_name,{})

        log.info("Executing agent:%s",agent_name)

        user_id = runtime.context.user_name
        user_memory_file = f"/memories/personal/{user_id}_USER_MEMORY.md"
        system_prompt = main_agent_system_prompt.format(user_memory_file=user_memory_file)                             
        session_entry = await self.mcp_manager.acquire("github_1")
        mcp_tools = session_entry.tools
        searchable_tools = [tool.name for tool in mcp_tools]
        interrupt = InterruptDefinition(session_entry.tools)


        if self.distructive_tools is None:
           self.distructive_tools = interrupt.save_distructive_tools()
           log.info("Calling self distructive function once ->%s",  self.distructive_tools)

        else:
            log.info("For second round self distructibe tools not called ->",self.distructive_tools)


        if not self.interrupt_on:
            self.interrupt_on = interrupt.define_interrupt_on()
            print("Calling interrupt function once ->%s",self.interrupt_on)
        else:
            print("For second round self interrput not called -> %s",self.interrupt_on )
        

        memory_wrapper, skills_wrapper = self.store_backend.policy_wrapper()
        

        try:
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
                                                                        "content": (
                                                                                    f"Task:\n{task}\n\n"
                                                                                    f"Relevant Context from Previous Agents:\n{content}\n\n"
                                                                                )
                                                                    }
                                                                ]
                                                },

                                                config = config,
                                                context = ContextSchema(user_id = user_id),)
    
         
            
            agent_output = result.get('structured_response')

            status = result.get(agent_output.status).lower()

            artifact_record = self.store_backend.store_agent_output(agent_name, user_id, agent_output )

            if agent_output and status == 'success':
                
                return {"artifacts_id" : {agent_name : artifact_record.artifact_id}, "successful_route_executed" : {route_id: agent_name}}
            else:
                return {"artifacts_id" : {agent_name : artifact_record.artifact_id}, "failed_route_executed" : {route_id: agent_name}}
            
        except GraphInterrupt:
            raise
           
        except Exception as exc:

            log.exception("Deep Agent execution failed")

            if is_broken_mcp_session(exc):

                await self.mcp_manager.discard_and_replace("github_1", session_entry)

                self.discarded = True

            else:
                raise

        finally:

            if self.ls_sandbox:
                self.client.delete_sandbox(self.ls_sandbox.name)

            if not self.discarded:
                await self.mcp_manager.release("github_1", session_entry)

    def fan_in_routes(self, state: CustomState):
        log.info(
            "Parallel route execution completed. Successful=%s Failed=%s",
                state.get("successful_route_executed", {}),
                state.get("failed_route_executed", {})
            )

        return {}

    def route_after_orchestrator(self, state: CustomState):

        if state.get("ready_routes"):
            return "revert_to_details_gathering_node"

        return "end_node"

     
    def state_tracking_after_deep_agent_execution(self, state: CustomState):

        ready_route = state["ready_routes"]

        log.info("State_Tracking_post_execution_of_ready_agents_%s:", ready_route)

        if state:
            
            log.info("ready_routes -> %s", state.get("ready_routes", "NA"))

            log.info("successful_route_executed -> %s",state.get("successful_route_executed", "NA"))

            log.info("failed_route_executed -> %s",state.get("failed_route_executed", "NA"))

            log.info("artifacts_id -> %s", state.get("artifacts_id", "NA"))

            log.info("context_given_agent ->%s ",state.get("context_given_agent", "NA"))

            log.info("routing_information ->%s ",state.get("routing_information", "NA"))

            log.info("user_request -> %s", state.get("user_request", "NA"))

            log.info("messages ->%s", state.get("messages", "NA"))

        return {}

    def store_tracking_after_deep_agent_execution(self, state:CustomState, runtime:Runtime):


        print('Store_contents_post_ready_agent_execution:%s',state["ready_routes"])

        user_id = runtime.context.user_id
    
        print("New_learning_updated in store", self.store_backend.read_agent_learning())
 
        print("User_memory_updated ->", self.store_backend.read_user_personal_memory(user_id))
        
    async def end_node(self,state:CustomState):
        log.info("Workflow completed. Closing MCP manager.")
        await self.mcp_manager.close()
        return {}





    



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