'''
addition()
    ↓
MCP Server registers/exposes it
    ↓
MCP Client can discover it

FastMCP is not the MCP protocol itself.
MCP = the standard/protocol — the rules for how clients and servers communicate.
FastMCP = a Python framework that makes it easy to build an MCP server following those rules.
MCPAdapter = LangChain's integration that connects to an MCP server and turns its tools into LangChain tools.
'''
from fastmcp import FastMCP #Give my Python program the FastMCP class so I can create an MCP server
from langchain.mcp import MCPAdapter #adpater is bridge between MCP server and langchain
import asyncio
from config.llm_config import llm_openai
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from uuid_utils import uuid7
from langgraph.types import Command
from langchain.tools import BaseTool
from langchain.agents.middleware.human_in_the_loop import InterruptOnConfig
from langchain.tools.tool_node import ToolCallRequest


mcp = FastMCP("Simple MCP Server") # Creates our MCP server.

@mcp.tool(annotations={"readOnlyHint": True}) # Registers a Python function as a tool on that server
def addition(a:int,b:int)-> int:
    if a or b is None:
        return "Provide numbers to add"
    return a+b

@mcp.tool(annotations={"destructive_hint": True}) # Registers a Python function as a tool on that server
def subtraction(a:int,b:int)-> int:
    return a-b

adapter = MCPAdapter(mcp) # FOr inprocess server, adapter can directly connect to mcp object. This will expose serverside tool to langchain

checkpointer = InMemorySaver()
config = {"configurable" : {"thread_id": str(uuid7())}}
destrcutive_tools = []

def find_destructive_tool(tool:BaseTool) -> bool:
    annotation = ( (tool.metadata or {}).get("mcp",{}).get("tool",{}).get('annotations',{}))
    return annotation.get("destructive_hint",False)

async def main():
    tools = await adapter.list_tools()
    #print(tools)
    #print(await tools[0].ainvoke({"a": 10, "b": 20}))

    destructive_tools = [tool.name for tool in tools if find_destructive_tool(tool)]
    print(destructive_tools)

    def needs_approval(request:ToolCallRequest) -> bool:
        return request.tool_call["name"] in destructive_tools

    gate = InterruptOnConfig(allowed_decisions=["approve","reject"], when = needs_approval)

    interrupt_on: dict[str: bool | InterruptOnConfig] = {tool.name: gate for tool in tools }
    print("Interrupt_on -> ",interrupt_on)

    #middleware = HumanInTheLoopMiddleware(interrupt_on = {"subtraction":True,"addition":False})
    middleware = HumanInTheLoopMiddleware(interrupt_on=interrupt_on)
    
    agent = create_agent(model = llm_openai, tools = tools,middleware = [middleware],
                         checkpointer=checkpointer,
                         system_prompt = "Use the subtraction tool to subtract 30 from 10")
  

    result = await agent.ainvoke({"messages" : [ {"role" : 'user', "content" : "Subtract 30 from 10"}
                                ]

                },
                config = config
                )

    print(result["__interrupt__"][0].value["action_requests"])
    print(result["__interrupt__"][0].value["review_configs"])

    while True:
        decision = input("Do you want to approve or reject this tool call? ").strip().lower()
        if decision in ["approve","reject"]:
            break
        
        print("Invalid input. Please enter 'approve' or 'reject'.")

    result = await agent.ainvoke(
    Command(resume={
            "decisions": [
                {"type": decision} #"reject"
            ]
        }
    ),
    config=config
    )         
  
    '''
    result = await agent.ainvoke(
    Command(
        resume={
            "decisions": [
                {
                    "type": "edit",
                    "edited_action": {
                        "name": "subtraction",
                        "args": {
                            "a": 30,
                            "b": 10
                        }
                    }
                }
            ]
        }
    ),
    config=config
)
    print("Result after human reply edit", result["messages"][2].artifact["structured_content"])
    print(result["__interrupt__"][0].value["action_requests"])
    print(result["__interrupt__"][0].value["review_configs"])
    result = await agent.ainvoke(
        Command(resume={
                "decisions": [
                    {"type": "approve"}
                ]
            }
        ),
        config=config
        )         
   
    '''
    print(result["messages"][-1].content)
if __name__ == "__main__":
    asyncio.run(main())
