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
from typing_extensions import Any
from app.schemas.agent_output_schema import AgentOutput
from langchain_core.messages import AIMessage, ToolMessage
from logger.log import setup_logging
log = setup_logging()

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

                Determine whether the experience contains a genuinely reusable lesson
                that could help an agent perform better in a future execution.

                A reusable lesson can be:

                - a mistake and how to avoid it
                - a failed approach and a better approach
                - a stable, reusable tool/environment/workspace constraint
                - a reusable procedure or pattern discovered during execution
                - a successful approach that is broadly reusable in future executions

                A learning must describe a reusable rule, pattern, constraint, mistake,
                or procedure — not merely report what happened during this execution.

                Do NOT create learning from temporary execution-specific facts such as:

                - file paths
                - commit SHAs
                - branch names
                - repository contents
                - tool output
                - logs
                - execution results
                - temporary state
                - task-specific values
                - artifacts

                Do not create a lesson merely because an execution was successful
                or produced an interesting result.

                If the experience contains no genuinely reusable information,
                return has_learning=false.

                If the same or substantially similar lesson already exists in
                Existing learning, return has_learning=false.

                Do not create a new lesson that merely restates, slightly rephrases,
                or narrows an existing general lesson unless it adds meaningfully
                new reusable information.

                If reusable learning exists, write it as a concise standalone lesson
                that can be added directly to LEARNINGS.md.

                Execution experience:
                {experience}

                Existing learning:
                {existing_learning}

               
                """
    learning_chain = ChatPromptTemplate.from_messages([("system",prompt)]) | structured_llm
    result = learning_chain.invoke({"experience" : experience,"existing_learning":existing_learning})
    return result

def detect_execution_event(messages):
    details = {"content": None, "tool_errors": []}
    for message in reversed(messages):
     
        if isinstance(message,AIMessage):
            content = message.content
            if details["content"] is None:
                details["content"] = content


        if isinstance(message,ToolMessage):
            if message.status == "error":
                content = message.content
                
                if isinstance(content, str):
                    details["tool_errors"].append(content)
                elif isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        if block.get("type") == "text":
                            text = block.get("text")
                            if text:
                                details["tool_errors"].append(text)


    return details

def normalize_agent_output(result:dict|Any) -> AgentOutput:
    try:
        # ---------------------------------------------------------
        # CASE 1: Deep Agent returned structured_response
        # ---------------------------------------------------------
        structured_response = result.get("structured_response")

        if isinstance(structured_response, AgentOutput):
            log.info("Agent returned output in structured response format")
            return structured_response

        if structured_response is not None:
            try:
                return AgentOutput.model_validate(structured_response)
            except Exception:
                log.exception("Structured response dont support the AgentOutput Schema")
                raise

        # ---------------------------------------------------------
        # CASE 2: No structured_response
        #         Try final AIMessage
        # ---------------------------------------------------------

        messages = result.get("messages", [])

        if not messages:
            return AgentOutput(
                status="Failed",
                summary="Agent completed without producing a response.",
                result=None,
                errors=["No messages returned by the agent."]
            )

        
        log.info("Agent gave output in terms of messages:%s",messages)
        
        details = detect_execution_event(messages)

        errors = []

        content = details.get("content",None)

        tool_errors = details.get("tool_errors",None)

        if tool_errors:
            errors.extend(tool_errors)
        
        # ---------------------------------------------------------
        # CASE 2A: content is a string
        # ---------------------------------------------------------
        if isinstance(content,str):
            log.info("Agent returned output in form of string")
            text = content.strip()
            #Try JSON first
            try:
                parsed = json.loads(text)
                return AgentOutput.model_validate(parsed)
            except(json.JSONDecodeError,ValueError,TypeError):
                pass

                   # Not JSON → treat it as normal agent output
            return AgentOutput(
                status="Partial_Success",
                result = text,
                errors = errors,
                metadata={
                    "output_source": "ai_message_text",
                    "structured_response_missing": True
                }
            )

        # ---------------------------------------------------------
        # CASE 2B: content is a list of content blocks
        # ---------------------------------------------------------
        if isinstance(content,list):
            log.info("Agent returned output in form of list")
            text_parts = []

            for block in content:
                if not isinstance(block,dict):
                    continue

                if block.get("type") == "text":
                    text = block.get("text")
                    if text:
                        text_parts.append(text)
            
            text = "\n\n".join(text_parts).strip()
            
            if text:

                # Try json
                try:
                    parsed = json.loads(text)
                    return AgentOutput.model_validate(parsed)
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass

                    return AgentOutput(
                                status="partial_success",
                                result = text,
                                errors = errors,
                                metadata={
                                    "output_source": "ai_message_text_blocks",
                                    "structured_response_missing": True
                                }
                            )

        # ---------------------------------------------------------
        # CASE 3: Nothing usable
        # ---------------------------------------------------------
        return AgentOutput(
            status="failed",
            summary="Agent did not produce a usable response.",
            result = None,
            errors=[
                    "structured_response was missing and final AIMessage contained no usable text.",
                    *errors
            ],
            metadata={"structured_response_missing": True}
        )
    except Exception:
        log.exception("Error occured while normalizing agent output")
        raise

        
            

    

    
    
    
