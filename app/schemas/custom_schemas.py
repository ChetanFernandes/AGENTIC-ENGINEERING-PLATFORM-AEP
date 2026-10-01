from typing import TypedDict , List , Any , Annotated
from langgraph.graph.message import add_messages
from app.executor.langgraph.reducer import merge_dicts ,merge_or_reset
from app.schemas.agent_output_schema import AgentOutput
from dataclasses import dataclass
from langchain.agents.middleware import AgentState
from pydantic import BaseModel
from app.router.schemas import RouteDecision

class CustomState(AgentState):

    final_answer: AgentOutput | None  
    artifacts_id: Annotated[dict[str , str] , merge_or_reset]  
    context_given_agent : dict[str , Any]
    tool_call_details : dict[str,int]
    routing_information : RouteDecision
    user_request:str
    ready_routes: list[dict[str, str]]
    successful_route_executed:Annotated[dict[str, str], merge_or_reset]
    failed_route_executed: Annotated[dict[str, str], merge_or_reset]

    current_route: dict[str, str]


    # Agent → produces AgentOutput → LangGraph node updates agents_outputs → 
    # Annotated tells LangGraph to use our reducer → shared state retains outputs from multiple agents.

class AgentInput(TypedDict):
    task:str
    content: Any
    resources: dict[str, Any]

@dataclass
class RuntimeContextSchema():
    user_id:str
    checkpointer:Any|None = None
    backend:object|None = None

class ArtifactRecord(BaseModel):
    artifact_id:str
    user_id:str
    agent:str
    storage_key:str




