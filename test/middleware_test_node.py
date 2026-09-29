from langchain.agents.middleware import AgentMiddleware
from app.schemas.custom_schemas import CustomState, ContextSchema
from langchain.agents import create_agent
from llm_config import llm_openai
from langchain.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from typing import Any


class ToolTracking(AgentMiddleware[CustomState]):
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


    def after_model(self,state:CustomState, runtime:ContextSchema):
        print("After_model_messages_after_model_call", state.get("messages", {}))
        print("After_model_tool_call_count",state.get("tool_call_details",0) + 1)
        return {"tool_call_details" : {"tool_a" : 1}, "model_call_count" : 2}


    def after_agent(self,state:CustomState, runtime:ContextSchema):
        print("AFTER AGENT STATE =", state)
        print("Amessages_after_agent_call", state.get("messages", {}))
        print("After_agent_tool_call_count",state.get("tool_call_details",0))

agent = create_agent(model = llm_openai, middleware=[ToolTracking()], state_schema = CustomState)

# Invoke with custom state

result = agent.invoke( 
                       {"messages": [HumanMessage("Hello")]}, 
                        context = ContextSchema(user_id=123) ,
                        config = {"configurable" : {"thread_id" : "888"}}
                        )
print("---"*100)
print("result", result)