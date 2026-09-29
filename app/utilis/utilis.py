from fastmcp import Client
from dotenv import load_dotenv
load_dotenv()
import os
from fastmcp.client.group import ClientGroup
from mcp import MCPError
from langchain.tools import BaseTool
from langchain.tools.tool_node import ToolCallRequest
from langchain.agents.middleware.human_in_the_loop import InterruptOnConfig
from typing import Annotated

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

