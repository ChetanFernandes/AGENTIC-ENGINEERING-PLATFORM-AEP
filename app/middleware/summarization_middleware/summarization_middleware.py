from deepagents.middleware import SummarizationMiddleware
from deepagents.middleware.summarization import create_summarization_tool_middleware
from config.llm_config import llm_openai        

def create_summarization_middleware(backend):
    custom_middleware = SummarizationMiddleware(model = llm_openai, backend= backend, trigger =[ ("tokens" , 4000),("messages",12)], keep=("messages", 8),
                            summary_prompt = 
                                                """
                                                You are maintaining execution state for a long-running AI agent.

                                                Create a concise but information-complete summary that allows the agent
                                                to continue execution without access to the older messages.

                                                Preserve the following sections:

                                                ## TASK
                                                - Original user objective
                                                - Current task being executed

                                                ## DECISIONS
                                                - Important decisions already made
                                                - Decisions that should not be revisited

                                                ## DISCOVERED INFORMATION
                                                - Important facts discovered through tools
                                                - Repository/code findings
                                                - Relevant MCP results

                                                ## TOOL EXECUTION
                                                - Important tools called
                                                - Important arguments
                                                - Important results
                                                - Failed tool calls and their resolutions
                                                - Tool calls currently in progress or awaiting execution

                                                ## ARTIFACTS
                                                - Important file paths
                                                - Repository paths
                                                - Artifact IDs
                                                - Created/modified resources

                                                ## CONSTRAINTS
                                                - User requirements
                                                - Technical constraints
                                                - Permissions or approval requirements

                                                ## PROGRESS
                                                Completed:
                                                - ...

                                                Pending:
                                                - ...

                                              ## INTERRUPTS / APPROVALS
                                                - Human approval/rejection decisions
                                                - Tool call that caused the interrupt
                                                - Exact tool name and arguments
                                                - Whether approval was granted, rejected, or still pending
                                                - Whether the approved tool has already executed
                                                - Important state required for resume

                                                ## NEXT STEP
                                                - The immediate next action the agent should take.
                                                - Do not restart completed work.
                                                - Do not repeat already completed tool calls unless required.

                                                Rules:
                                                - Do not invent information.
                                                - Do not execute tools.
                                                - Do not repeat unnecessary conversational content.
                                                - Preserve exact identifiers, paths, tool names, branch names, and artifact IDs.
                                                - Preserve information required to resume execution correctly.
                                                """
                                                )
    return custom_middleware


def create_summarization_middleware_deepagent(backend):
    custom_middleware_deep_agent = create_summarization_tool_middleware(model = llm_openai, 
                            backend= backend, 
                            #trim_tokens_to_summarize = None,
                            system_prompt = """
                                                You are maintaining execution state for a long-running AI agent.

                                                Create a concise but information-complete summary that allows the agent
                                                to continue execution without access to the older messages.

                                                Preserve the following sections:

                                                ## TASK
                                                - Original user objective
                                                - Current task being executed

                                                ## DECISIONS
                                                - Important decisions already made
                                                - Decisions that should not be revisited

                                                ## DISCOVERED INFORMATION
                                                - Important facts discovered through tools
                                                - Repository/code findings
                                                - Relevant MCP results

                                                ## TOOL EXECUTION
                                                - Important tools called
                                                - Important arguments
                                                - Important results
                                                - Failed tool calls and their resolutions
                                                - Tool calls currently in progress or awaiting execution

                                                ## ARTIFACTS
                                                - Important file paths
                                                - Repository paths
                                                - Artifact IDs
                                                - Created/modified resources

                                                ## CONSTRAINTS
                                                - User requirements
                                                - Technical constraints
                                                - Permissions or approval requirements

                                                ## PROGRESS
                                                Completed:
                                                - ...

                                                Pending:
                                                - ...

                                              ## INTERRUPTS / APPROVALS
                                                - Human approval/rejection decisions
                                                - Tool call that caused the interrupt
                                                - Exact tool name and arguments
                                                - Whether approval was granted, rejected, or still pending
                                                - Whether the approved tool has already executed
                                                - Important state required for resume

                                                ## NEXT STEP
                                                - The immediate next action the agent should take.
                                                - Do not restart completed work.
                                                - Do not repeat already completed tool calls unless required.

                                                Rules:
                                                - Do not invent information.
                                                - Do not execute tools.
                                                - Do not repeat unnecessary conversational content.
                                                - Preserve exact identifiers, paths, tool names, branch names, and artifact IDs.
                                                - Preserve information required to resume execution correctly.
                                                """)
                            
    return custom_middleware_deep_agent 