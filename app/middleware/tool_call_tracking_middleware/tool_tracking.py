from langchain.agents.middleware import AgentMiddleware
from typing import Callable, Any
from langgraph.prebuilt.tool_node import ToolCallRequest
from langchain.messages import ToolMessage
from langgraph.types import Command
from langchain.agents.middleware import ModelRequest,ModelResponse,ExtendedModelResponse
from langchain.messages import ToolMessage,AIMessage
from config.llm_config import llm_openai_mini
from pprint import pprint
import json
from app.schemas.custom_schemas import CustomState
from pydantic import BaseModel
from app.utilis.utilis import extract_learning

from langgraph.runtime import Runtime
from langchain.tools import tool, ToolRuntime
#from langchain.agents.middleware import before_model, after_model, AgentState, before_agent, after_agent

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

        messages = state.get("messages", [])
        if not messages:
            print("Before_agent: no messages in state")
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

        print("RESPONSE_type:", type(last_message).__name__)

    
        # ---------------------------------------------------------
        # Case 1: ToolMessage
        # ---------------------------------------------------------
        if isinstance(last_message, ToolMessage):
            print("Message is ToolMessage")
            print("\nTOOL MESSAGE CONTENT:")
            print(last_message.content)
            print("-" * 50)

        # ============================================================
        # CASE 2: AIMessage
        # ============================================================
        elif isinstance(last_message,AIMessage):
            print("Message is AIMessage")
            content = last_message.content
            # --------------------------------------------------------
            # AIMessage -> string
            # --------------------------------------------------------
            if isinstance(content,str):
                print("AIMessage content is string")
                try:
                    data = json.loads(content)

                    print("JSON_type_data")
                    print(data)

                except json.JSONDecodeError:

                    print("\nAI RESPONSE:")
                    print(content)

     
        # --------------------------------------------------------
        # AIMessage -> content blocks
        # --------------------------------------------------------
            elif isinstance(content,list):
                texts = []
                found_tool_call = False
                for block in content:
                    block_type = block.get("type")
                    if block_type == "text":
                        text = block.get("text")
                        if text:
                            texts.append(text)

                    elif block_type == "function_call":
                        found_tool_call = True
                        print("LLM called tool:", block.get("name"))

                    elif block_type == "reasoning":
                        pass
            if texts:
                print("\n AI Response \n")
                print("\n".join(texts))

            if found_tool_call:
                print("\nLLM called tool(s)")

            if not texts and not found_tool_call:

                print("\nNo text or tool call found in AIMessage.")

        
        # ============================================================
        # UNKNOWN MESSAGE TYPE
        # ============================================================

        else:

            print("Unhandled message type:",
                type(last_message).__name__
            )

            print("Content:")
            print(last_message.content)



    # ============================================================
    # TOKEN USAGE
    # ============================================================
        
        print("\n")
        print("Token Details\n")
        token_usage = getattr(last_message, "usage_metadata", None)
        if token_usage:

            print("Input_Token_consumed ->", token_usage.get("input_tokens"))

            print("Output_Token_consumed ->", token_usage.get("output_tokens"))

            print("Total_Token_consumed ->", token_usage.get("total_tokens"))

            print("Output_Token_details ->", token_usage.get("output_token_details"))

            print("Input_Token_details ->",token_usage.get("input_token_details"))

        else:
            print("No token details found")

        print("\n")
            
      
      
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
            print("Tool call status ->",response.status)
            print("Tool_response -> \n",str(response.content[:500]))
        
            self.execution_events.append({  
                                            "type" : "tool_result",
                                            "tool":   response.name or request.tool_call["name"],
                                            "status": response.status,
                                            "result": response.content
                                        })
        else:
            self.execution_events.append({
            "type": "tool_result",
            "tool": request.tool_call["name"],
            "status": "unknown",
            "result": repr(response)
        })

        return response

      
    def after_agent(self,state:CustomState):
        try:

            print("\n")
            print("Deep_agent_state_after_agent")
            print("-" * 70)

            existing_learning = ""

            try:

                existing_learning =  self.store_backend.read_agent_learning()
                if existing_learning is None:
                    existing_learning = ""
                
                log.info("Successfully extracted existing learning")

            except FileNotFoundError:
                log.info("LEARNINGS.md not available yet")

            except Exception:
                log.info("learning.MD not availabe yet")

     
            learning = extract_learning(self.execution_events, existing_learning, llm_openai_mini, LearningOutput)
            log.info("Successfully extracted new learning")

            log.info("Learning extraction completed")

            if learning.has_learning and learning.learning:

                new_learning = learning.learning.strip()

                if existing_learning.strip():
                    updated_learning = (
                                    f"{existing_learning.rstrip()}\n\n{new_learning}")
                else:
                    updated_learning = new_learning

                log.info("Updating new learning stored in the store")
                self.store_backend.write_learning(updated_learning)
                log.info("New learning stored in the store")
            else:
                pass

        except Exception:
            log.exception("Error occured in after agent")
         


    


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
