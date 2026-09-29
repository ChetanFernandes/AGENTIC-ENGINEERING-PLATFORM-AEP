from langchain.agents.middleware import AgentMiddleware, AgentState
from langgraph.types import Command
from app.schemas.custom_schemas import CustomState
from langchain.tools import tool, ToolRuntime


class ToolCallTrackingState(AgentState):
    tool_call_details: dict            # I created a state schema for the Deep Agent.
    ## AgentState already contains the normal state fields that an agent needs, such as messages. We added extra fields tool_call_details

class ToolCallTrackingMiddleware(AgentMiddleware[AgentState]): # This is your middleware. It intercepts the tool calls.

    state_schema = ToolCallTrackingState 
    # "When this middleware is installed in the Deep Agent, include ToolCallTrackingState as part of the Deep Agent's state schema."
 
    def wrap_tool_call(self, request, handler):

        runtime = request.runtime

        tool_name = request.tool_call['name']
        tool_args = request.tool_call["args"]

        #current state details

        print("[Middleware] Deep_agent_State keys:", runtime.state.keys())
    
        print("[Middleware] Deep_agent_state:", runtime.state)

        current_state = runtime.state.get("tool_call_details",{})

        print("deep_agent_current_state for field tool_call_details", current_state)

        # take copy of current state
        current_state_copy = current_state.copy()

        current_state_copy[tool_name] = current_state_copy.get(tool_name,0) + 1

        print("deep_agent_current_state_copy",current_state_copy)

        print(f" Tool called: \n{tool_name} :  {current_state_copy[tool_name]}")

        print(f"[Middleware] Arguments: {tool_args}")

        result = handler(request)

        # print(f"[Middleware] Result type: {type(result)}")

        print(f"[Middleware] Tool call {tool_name} completed")

        return Command(update={"tool_call_details" : current_state_copy, 
                               'messages' : [result]
                                }
                      )


'''
When LangChain invokes your wrap_tool_call, it constructs a ToolCallRequest object and passes it to your middleware. 
That request contains information about the current tool execution, including the current agent state.

LangGraph execution
        │
        │ current state
        ▼
CustomState
{
    "messages": [...],
    "agent": "...",
    "task": "...",
    "tool_call_details": {...}
}
        │
        │ LangChain builds request
        ▼
ToolCallRequest
{
    tool_call: {
        "name": "read_file",
        "args": {...}
    },
    state: CustomState,
    runtime: ...
}
        │
        ▼
wrap_tool_call(request, handler)
'''














