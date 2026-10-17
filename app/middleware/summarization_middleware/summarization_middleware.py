from deepagents.middleware.summarization import (SummarizationMiddleware, DEEPAGENTS_DEFAULT_SUMMARY_PROMPT,)
    
system_prompt = """
You are summarizing conversation history for a multi-agent AI platform.

Your goal is to preserve the information the current agent needs
to continue its assigned task accurately and efficiently.

## TASK AND OBJECTIVE
- Preserve the original user request and current agent's assigned task.
- Preserve the objective, scope, requirements, and expected output.
- Preserve completed work and the immediate next step.
- Do not replace the original task with a history-recovery task.

## DISCOVERIES AND DECISIONS
- Preserve relevant findings, evidence, decisions, and constraints.
- Preserve exact file paths, identifiers, artifact IDs, tool names,
  branch names, and other execution-critical references.
- Preserve relevant upstream-agent findings and tool results.
- Distinguish confirmed facts from assumptions and unresolved questions.

## EXECUTION STATE
- Preserve important actions, outcomes, errors, and their resolutions.
- Identify completed and pending work.
- Preserve approval requests, interruptions, and their current status.
- Avoid repeating completed work unnecessarily.

## FIDELITY
- Use only information supported by the available conversation.
- Do not invent facts, paths, identifiers, results, or events.
- Do not turn uncertainty into certainty.
- Do not omit failures or limitations that affect continuation.
- Preserve the meaning of the original task and user requirements.
- Do not introduce new objectives or instructions.
- Distinguish information unavailable in the current context from
  information confirmed to be absent from the original conversation.
- Preserve existing conversation-history paths exactly when present.
- Include historical recovery details only when relevant.

Return a concise, execution-ready summary that allows the current
agent to continue its assigned task.
"""

summary_prompt_final = ( DEEPAGENTS_DEFAULT_SUMMARY_PROMPT + "\n\n" + system_prompt)


def create_summarization_middleware(backend,llm_openai):
    custom_middleware = SummarizationMiddleware(model = llm_openai, backend= backend, trigger =[ ("tokens" , 20000),("messages",20)], keep=("messages", 10),
    summary_prompt = summary_prompt_final)                                                                             
    return custom_middleware

'''
from deepagents.middleware.summarization import create_summarization_tool_middleware
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
  '''