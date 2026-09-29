from typing import Callable
from langchain.agents.middleware import (wrap_model_call,ModelRequest,ModelResponse,AgentState,ExtendedModelResponse)
from langgraph.types import Command
from typing import NotRequired
from app.schemas.custom_schemas import CustomState
from langchain.agents.middleware import AgentMiddleware
from langchain.agents import create_agent
from llm_config import llm_openai
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from app.schemas.custom_schemas import ContextSchema
from typing import TypedDict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt.tool_node import ToolCallRequest, ToolCallWrapper


class tool_tracking(AgentMiddleware[CustomState]):
    def __init__(self):
         super().__init__()

    def before_agent(self,state:CustomState) -> dict[str|Any] | None:
        print("Amessages_before_agent_call", state)
        print(type(state))

    def before_model(self, state:CustomState, runtime:ContextSchema, config : RunnableConfig) -> dict[str|Any] | None:
        print("Bmessages_before_model_call", state.get("messages", {}))
        print("Bmodel_call_count", state.get("model_call_count",0))
        print("Bbefore_agent", state.get("task","NA"))
        print("Btool_call_count",state.get("tool_call_details",0))
        print("BruntIme_user_is",runtime.context.user_id)
        print("Bruntine_config", config["configurable"]["thread_id"])
        return {"messages" : HumanMessage("What is capital of India")}

    
    def wrap_model_call(self,request:ModelRequest, handler: Callable[[ModelRequest], ModelResponse]) -> ExtendedModelResponse:
        print("BEFORE MODEL")
        print("MODEL:", request.model)
        print("SYSTEM:", request.system_prompt)
        print("MESSAGES:", request.messages)
        print("TOOLS:", request.tools)
        print("STATE:", request.state.get("model_call_count",0))
        print("RUNTIME:", request.runtime)
        print("CONTEXT:", request.runtime.context.user_id)
        new_request = ModelRequest(model = llm_openai,messages= [HumanMessage("What is capital of India")])
        #return handler(request.override(messages = new_request.messages))
        request.messages.extend(new_request.messages)
        response = handler(new_request)
        print("AFTER MODEL")
        print("RESPONSE",response)
        #response = ModelResponse(result=[AIMessage(content="Chetan")])
        #print("RESPONSE_updated",response)
                                 
        return ExtendedModelResponse(model_response = response, command=Command(update={"model_call_count": 150}),)

    
    def after_model(self,state:CustomState):
        print("ContextSchema", state.get("model_call_count"))
        print("message",state["messages"][-1].response_metadata["token_usage"])

    def wrap_tool_call(self,request:ToolCallRequest, handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]]) -> ToolMessage | Command[Any]:
        print("BEFORE MODEL")
        print("MODEL:", request.model)
        print("SYSTEM:", request.system_prompt)
        print("MESSAGES:", request.messages)
        print("TOOLS:", request.tools)
        print("STATE:", request.state.get("model_call_count",0))
        print("RUNTIME:", request.runtime)
        print("CONTEXT:", request.runtime.context.user_id)
        new_request = ModelRequest(model = llm_openai,messages= [HumanMessage("What is capital of India")])
        request.messages.extend(new_request.messages)
        response = handler(new_request)
        print("AFTER MODEL")
        print("RESPONSE",response)
        #response = ModelResponse(result=[AIMessage(content="Chetan")])
        #print("RESPONSE_updated",response)
                                    
        return ExtendedModelResponse(model_response = response, command=Command(update={"model_call_count": 150}),)

    def before_model(self):
        pass

    def wrap_model_call(self,config : RunnableConfig):
        print("wrap_model_call", config["configurable"]["thread_id"])

    def after_model(self):
        pass

    
    def after_agent(self,state:CustomState, runtime:ContextSchema):
        print("AFTER AGENT STATE =", state)
        print("Amessages_after_agent_call", state.get("messages", {}))
        print("After_agent_tool_call_count",state.get("tool_call_details",0))
    



     
agent = create_agent(model = llm_openai, middleware=[tool_tracking()], state_schema = CustomState)

# Invoke with custom state

result = agent.invoke( 
                       {"messages": [HumanMessage("Hello")]}, 
                        context = ContextSchema(user_id=123) ,
                        config = {"configurable" : {"thread_id" : "888"}}
                        )
print("---"*100)
print("result", result)