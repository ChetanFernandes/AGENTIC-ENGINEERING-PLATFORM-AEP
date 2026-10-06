
from dotenv import load_dotenv
load_dotenv()
from mcp import MCPError
import json
from langchain_core.prompts import ChatPromptTemplate
from typing_extensions import Any
from app.schemas.agent_output_schema import AgentOutput
from langchain_core.messages import AIMessage, ToolMessage
from deepagents.backends import LangSmithSandbox
from logger.log import setup_logging
log = setup_logging()


def is_broken_mcp_session(exc: Exception) -> bool:
    """ To check is currect MCP session is broken or not"""

    if isinstance(exc, MCPError):

        message = str(exc).lower()

        if "session not found" in message:
            return True

    return False


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
    """ To extract content and error in case final output returned by message is not structured response"""
    details = {"AI_content": None, "Tool_content":None, "tool_errors": []}

    for message in reversed(messages):
     
        if isinstance(message,AIMessage):
            content = message.content
            if details["AI_content"] is None:
                details["AI_content"] = content

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
    """ To normalize final agent output"""
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

        AI_content = details.get("AI_content",None)

        tool_errors = details.get("tool_errors",None)

        if tool_errors:

            errors.extend(tool_errors)
        
        # ---------------------------------------------------------
        # CASE 2A: content is a string
        # ---------------------------------------------------------
        if isinstance(AI_content,str):
            log.info("Agent returned output in form of string")
            text = AI_content.strip()
            #Try JSON first
            try:
                parsed = json.loads(text)
                return AgentOutput.model_validate(parsed)
            except(json.JSONDecodeError,ValueError,TypeError):
                pass

                   # Not JSON → treat it as normal agent output
            return AgentOutput(
                status="partial_success",
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
        if isinstance(AI_content,list):
            log.info("Agent returned output in form of list")
            text_parts = []

            for block in AI_content:
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

        
            
def format_previous_question(previous_messages:list,current_question):
    requests = []
    for message in previous_messages:
        if message != current_question:
                requests.append(message)

    return "\n\n".join(f"previous_requests: {i+1}: {message}" for i, message in enumerate(requests))

def sandbox_provision(client):
    sandboxes = client.list_sandboxes()
    ls_sandbox = next((sandbox for sandbox in sandboxes if sandbox.name =="aep-sandbox"),None)
    log.info("List of existing sandbox:%s",  ls_sandbox)

    if  ls_sandbox:
        status =  client.get_sandbox_status(ls_sandbox.name)
        log.info("status of Sandbox:%s",status.status)

    if ls_sandbox and status.status in ("running","ready","idle","provisioning"):
        log.info("Reusing Sandbox:%s", ls_sandbox.name)

    elif ls_sandbox and status.status == "stopped":
        client.start_sandbox(ls_sandbox.name, timeout=600)
        log.info("Sandbox started successfully:%s", ls_sandbox.name)

    elif ls_sandbox and status.status == "failed":
        client.delete_sandbox(ls_sandbox.name)
        ls_sandbox = client.create_sandbox(name="aep-sandbox")
        log.info("Failed Sandbox deleted and created new one:%s", ls_sandbox.name)

    else:
        ls_sandbox = client.create_sandbox(name="aep-sandbox")
        log.info("Created sandbox -> %s", ls_sandbox.name)

    sandbox_backend = LangSmithSandbox(sandbox = ls_sandbox)
    return sandbox_backend , ls_sandbox
        
    

    
    
    
