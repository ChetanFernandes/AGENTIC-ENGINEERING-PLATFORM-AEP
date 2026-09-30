from fastmcp import Client
from dotenv import load_dotenv
load_dotenv()
import os
from fastmcp.client.group import ClientGroup
from mcp import MCPError
from langchain.tools import BaseTool
from langchain.tools.tool_node import ToolCallRequest
from langchain.agents.middleware.human_in_the_loop import InterruptOnConfig
import json
from langchain_core.prompts import ChatPromptTemplate


token = os.getenv("GITHUB_ACCESS_TOKEN")

def create_github_client():
    return Client("https://api.githubcopilot.com/mcp/", auth=token,  mode="auto")

client_factories = {"github_1": create_github_client, "github_2": create_github_client,}

client_group = ClientGroup({"github_1":create_github_client(),"github_2":create_github_client()})


def is_broken_mcp_session(exc: Exception) -> bool:

    if isinstance(exc, MCPError):

        message = str(exc).lower()

        if "session not found" in message:
            return True

    return False


class InterruptDefinition:

    def __init__(self, tools):
        self.tools = tools
        self.distructive_tools = []

        self.mutation_tools = [
                "create_branch",
                "push_files",
                "create_or_update_file",
                "create_pull_request",
        ]

    def find_destructive_tool(self,tool:BaseTool) -> bool:
        annotation = ( (tool.metadata or {}).get("mcp",{}).get("tool",{}).get('annotations',{}))
        return annotation.get("destructive_hint",False)

    def save_distructive_tools(self):
        self.distructive_tools = [tool.name for tool in self.tools if self.find_destructive_tool(tool)]
        return self.distructive_tools


    def needs_approval(self,request:ToolCallRequest) -> bool:
        tool_name = request.tool_call["name"]

        if tool_name in self.distructive_tools:
            return True
        if tool_name in self.mutation_tools:
            return True

        return False


    def define_interrupt_on(self):
        gate = InterruptOnConfig(allowed_decisions=["approve","reject"], when = self.needs_approval)
        approval_tools = set(self.distructive_tools) | set(self.mutation_tools)
        #print("Approval Tools",approval_tools)
        interrupt_on: dict[str: bool | InterruptOnConfig] = {tool_name: gate for tool_name in approval_tools}
        return interrupt_on


def print_agent_output(agent_output):
    data = agent_output.model_dump()
    print("\n" + "=" * 70)
    print("AGENT EXECUTION RESULT")
    print("=" * 70)
    print(f"\nStatus:\n{data.get('status')}")
    print(f"\nSummary:\n{data.get('summary')}")
    print(f"\nResult:\n{data.get('result')}")
    errors = data.get("errors")

    if errors:
            print("\nErrors:")
            for error in errors:
                print(f"  - {error}")

    metadata = data.get("metadata")

    if metadata:
            print("\nMetadata:")
            print(json.dumps(metadata,indent=2, ensure_ascii=False))

    print("=" * 70)



def extract_learning(experience, existing_learning,llm_openai,LearningOutput):

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
