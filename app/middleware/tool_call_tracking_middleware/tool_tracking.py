from langchain.agents.middleware import AgentMiddleware
from typing import Callable, Any
from langgraph.prebuilt.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langgraph.types import Command
from langchain.agents.middleware import ModelRequest,ModelResponse,ExtendedModelResponse
from langchain.messages import ToolMessage, AIMessage
from config.llm_config import llm_openai
from pprint import pprint
import json
from langgraph.runtime import Runtime
from langchain.tools import tool, ToolRuntime
from app.schemas.custom_schemas import CustomState
##from langchain.agents.middleware import before_model, after_model, AgentState, before_agent, after_agent
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from logger.log import setup_logging
log = setup_logging()

class LearningOutput(BaseModel):
    has_learning:bool
    learning:str| None = None

class state_Tool_Tracking(AgentMiddleware):
    
    def __init__(self, store, backend):
        super().__init__()
        self.store = store
        self.execution_events = []
        self.store_backend = backend
        self.turn:int = 0

    def before_agent(self,state:CustomState):
        print("\n")
        print("Deep_agent_state_information_before_agent \n")
        print("_"*50)
        print("state",state)
        messages = state.get("messages", [])

        if not messages:
            print("⚠️ before_agent: no messages in state")
            return state

        message = messages[-1]
        content = message.content

        parts = content.split("Task:", 1)
        human_message = parts[0].strip()
        task_and_context = parts[1]
        task,relevant_context = task_and_context.split("Relevant Context from Previous Agents:",1)

        human_message = human_message.removeprefix("messages:").strip()
        task = task.strip()
        relevant_context = relevant_context.strip()

        print("Human MESSAGE: \n") 
        pprint(human_message)

        print("-"*50) 
        print("Task: \n")
        pprint(task)

        print("-"*50) 
        print("Content: \n")
        pprint(relevant_context)
    
    ''' 
    def before_model(self, state):
        print("\n")
        print("Deep_agent_state_information_before_model \n")
        print("-"*50)
        self.turn += 1
        for message in (state["messages"]):
            if isinstance(message,AIMessage):
                print("MESSAGE TYPE:", type(message).__name__)
                print("Turn",self.turn)

            
                print("AI Message")
                pprint(message.content)

                print("Token Details")
                Token_usage = message.usage_metadata
        
                print("Input_Token_consumed")
                pprint(Token_usage["input_tokens"])  
        
                print("-"*50)    
        
                print("Output_Token_consumed")
                pprint(Token_usage["output_tokens"])
        
                print("-"*50)  
        
                print("Total_Token_consumed")
                pprint(Token_usage["total_tokens"])
        
                print("-"*50) 
                print("Output_Token_details")
                pprint(Token_usage["output_token_details"])
        
                print("-"*50) 
                print("Input_Token_details")
                pprint(Token_usage["input_token_details"])
        
                pass

            if isinstance(message, ToolMessage):
                print("Turn",self.turn)
                print("MESSAGE TYPE:", type(message).__name__)
                print("Tool response")
                pprint(message.content[:100])

                print("Tool Name")
                pprint(message.name)

            else:
                print("Turn",self.turn)
                print("First Iteration - Model not yet called")
            '''

            
    
    async def awrap_model_call(self, request:ModelRequest, handler: Callable[[ModelRequest], ModelResponse]) -> ExtendedModelResponse:
        #print("BEFORE MODEL CALL")
        #print("MODEL:", request.model)
        #print("SYSTEM:", request.system_prompt)
        #print("MESSAGES:", request.messages)
        #print("TOOLS:", request.tools)
        #print("RUNTIME:", request.runtime)
        #print("CONTEXT:", request.runtime.context.user_id)
        #print("\n🔥🔥🔥 MODEL CALL STARTED 🔥🔥🔥")
        #print("MODEL:", request.model)
        #print("NUMBER OF MESSAGES:", len(request.messages))
        #print("TOOLS GIVEN TO MODEL:", [tool.name for tool in request.tools])
        response = await handler(request)
        #print("\n🔥🔥🔥 MODEL CALL COMPLETED 🔥🔥🔥")
        #print("MODEL RESPONSE:", response)
        #print("Deep_agent_state_information_after_model", request.state)
        #print("AFTER MODEL")
        #print("RESPONSE",response)
        return ExtendedModelResponse(model_response = response)
       

    def after_model(self, state):
        print("\n")
        print("Deep_agent_state_information_after_model \n")
        print("-"*50) 

        last_message  = state["messages"][-1]

        if isinstance(last_message.content, str):

            try:
                print("Last message is string")

                data = json.loads(last_message.content)

                print("JSON_type_data",data)

                if "status" in data:
                    print("JSON_type_data", data["status"])

            except json.JSONDecodeError:
                print("error occured")
                print("AI_Message", last_message.content)

        else:   
                print("AI_RESPONSE",type(last_message).__name__)

                if last_message.content:
                        
                    print("AI_Message ->", last_message.content)
                else:
                    print("AI_Message ->", "LLM called tools")
    
  
        
        '''
        # ============================================================
        # TOOL CALLS
        # ============================================================

        if hasattr(last_message,"tool_calls") and last_message.tool_calls:
            print("\n")
            print("TOOL_CALL_DETAILS:\n")
        
            for tool_call in last_message.tool_calls:

                print("Task_Name->",tool_call["name"])
            
                print("Task_Description->",tool_call["args"])
        
                self.execution_events.append({  "type":"tool_call",
                                                    "tool":tool_call["name"],
                                                    "args":tool_call["args"]
                                                })
        else:
            print("No tool calls")
        '''


# ============================================================
# TOKEN USAGE
# ============================================================
    
        print("\n")

        print("Token Details\n")

        Token_usage = getattr(last_message, "usage_metadata", None)

        if Token_usage:

            print("Input_Token_consumed ->", Token_usage["input_tokens"])  
            print("-"*50)    

            print("Output_Token_consumed ->",Token_usage["output_tokens"])
            print("-"*50)  

            print("Total_Token_consumed->",Token_usage["total_tokens"])
            print("-"*50) 

            print("Output_Token_details->",Token_usage["output_token_details"])

            print("-"*50) 
            print("Input_Token_details->",Token_usage["input_token_details"])

        else:
            print("No token details found")
      
      
    async def awrap_tool_call(self, request:ToolCallRequest, handler:Callable[[ToolCallRequest],  ToolMessage | Command[Any]] ) -> ToolMessage | Command[Any]:

        print("*"*50)
        print("Tool_call_request_made_by_LLM\n")
        print("*"*50)

        print("Tool_name ->", request.tool_call['name'])
        print("Tool_arguments ->",request.tool_call['args'])
        print("Tool_call_id ->", request.tool_call["id"])
        print("Tool_call_type ->", request.tool_call["type"])
        print("\n")

        #print("Actual tool object: Worker")
        #print("\n")
        #print("Tool_name ->\n", request.tool.name)
        #print("Tool_description_given_to_LLM_by_FilesystemMiddleware ->\n", request.tool.description)
        #print("\n")
        #print("Tool_arguments_schema (This defines what arguments read_file accepts) ->", request.tool.args_schema)
        #print("\n")
        #print("Actual Python function that gets executed for the tool",request.tool.func)

        response = await handler(request)

        print("\n")

        print("*"*50)
        print("Tool_Response\n")
        print("*"*50)

        if isinstance(response, ToolMessage):

            print("Tool_content",response.name)
            print("Tool_response \n",response.content[:100])

            self.execution_events.append({  
                                            "type" : "tool_result",
                                            "tool":   response.name,
                                            "result": response.content
                                        })
        else:
              self.execution_events.append({
                "type": "tool_result",
                "tool": request.tool_call["name"],
                "result":  repr(response)
            })

        return response

      
    def after_agent(self,state):

        print("Deep_agent_state_after_agent \n")

        #print("self_learning_Events_captured", self.execution_events)

        print("State keys ->", state.keys())

        structured_response = state.get("structured_response")

        print("Structured response ->", structured_response)
 
        if structured_response is None:
            print("⚠️ structured_response is None")
            return
         

        print("Status -> ",structured_response.status)

        print("Summary ->",structured_response.summary)

        print("Result -> ", structured_response.result)
   

        print("Errors\n")

        pprint(structured_response.errors)

        print("Metadata")

        pprint(structured_response.metadata)

        #print("Memory Contents \n")
        
        #pprint(state["memory_contents"])

        existing_learning = ""
        try:
            existing_learning =  self.store_backend.read_agent_learning()
            #existing_learning += "\nWhen working on repository tasks, verify the current git branch before making changes"

        except Exception:
            log.info("learning.MD not availabe yet")

        print("Existing_learning",existing_learning)

        learning = self.extract_learning(existing_learning)

        print("New_Learning->\n",learning.learning)

        if learning.has_learning and learning.learning:
            updated_learning = f"{existing_learning}\n\n{learning.learning}"
            self.store_backend.write_learning(updated_learning)
        else:
            pass

        print("New_learning_updated in store", self.store_backend.read_agent_learning())


    def extract_learning(self,existing_learning):

        experience = self.execution_events

        structured_llm = llm_openai.with_structured_output(LearningOutput, method = "function_calling")

        prompt = """
                    You analyze an agent's execution experience.

                    Determine whether the experience contains a reusable lesson that could
                    help the agent perform better in a future execution.

                    A reusable lesson can be:
                    - a mistake and how to avoid it
                    - a failed approach and a better approach
                    - an environment/workspace discovery that reveals a reusable
                      pattern or constraint for future executions
                    - a successful approach worth repeating
                    
                    
                    Do not create learning from temporary execution-specific facts,
                    such as paths, commit SHAs, repository contents, tool output,
                    or other values that are unlikely to remain valid in future executions.


                    Do not create a lesson if the experience contains nothing reusable.

                    If the same or substantially similar lesson already exists in Existing learning,
                    do not create a new lesson and return has_learning as false.

                    If there is reusable learning, write it as a concise standalone lesson
                    that can be added directly to LEARNINGS.md

                    Execution experience:
                    {experience}

                    Existing learning:
                    {existing_learning}
                    """
        learning_chain = ChatPromptTemplate.from_messages([("system",prompt)]) | structured_llm
        result = learning_chain.invoke({"experience" : experience,"existing_learning":existing_learning})
        return result




'''
Hook	                     Good for
before_agent	                ✅ Check initial state, runtime, store, context
before_model	                Inspect what is about to be sent to the LLM
after_model	                    Inspect the LLM's response, tokens, tool calls
wrap_model_call	                Intercept/modify a model request or response
wrap_tool_call	                Intercept a specific tool invocation
after_agent	                    Inspect the final agent state/result
'''


'''
    ai_message = request.state["messages"][-1]
    tool_call =  ai_message.tool_calls[0]
    if tool_call["name"] == "task":
        desc = tool_call["args"]["description"]
        new_message = ("Repo link - 'https://github.com/ChetanFernandes/Advanced-Agentic-Multimodal-RAG'."
                    "Clone this repo under folder - /workspace." 
                    "Dont search for repo under /workspace.")
    tool_call["args"]["description"] = desc + "\n" + new_message 

'''
