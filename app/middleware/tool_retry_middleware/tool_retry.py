from langchain.agents.middleware import ToolRetryMiddleware, ToolErrorMiddleware , ModelRetryMiddleware , ModelCallLimitMiddleware
from langchain.agents.middleware import ToolCallLimitMiddleware
from langgraph.prebuilt.tool_node import ToolCallRequest


#--------------------Tool_Middleware------------------------------------------------------

def on_error(exc:Exception,request:ToolCallRequest) -> str|None:
    tool_name = request.tool_call["name"]
    if isinstance(exc,(ValueError,FileNotFoundError)):
        return (
                f"Tool '{tool_name}' failed with"
                f"{type(exc).__name__}. "
                "Review the tool result and correct the arguments or choose another approach"
        )
    return None

def tool_error_retry_middleware():
    
    Tool_retry_error_middleware = [ ToolRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=2.0, max_delay=60.0, jitter=True, tools = None,
                                                  retry_on=(ConnectionError, TimeoutError), on_failure= "error",),
                                    
                                    ToolErrorMiddleware(on_error=on_error),]

    return Tool_retry_error_middleware

#---------Model_Middleware---------------------------------------------------------------


def model_error_middleware():

    model_middleware_ = ModelRetryMiddleware( max_retries=3, backoff_factor=2.0, initial_delay=1.0, 
                                                          retry_on = "default_retry_on", on_failure = "error",) 
    return model_middleware_

#-----------------Model_Call_Limit--------------------------------------------------------


def model_call_limit_middleware():

    model_call_limit_middleware_ = ModelCallLimitMiddleware(thread_limit = 20, run_limit = 8, exit_behavior= "error",) 

    return model_call_limit_middleware_

#---------------------Tool_call_Limit----------------------------

def tool_call_limit_middleware():

    tool_call_limit_middleware_ = ToolCallLimitMiddleware(thread_limit = 20, run_limit = 8, exit_behavior= "continue",) 

    return tool_call_limit_middleware_