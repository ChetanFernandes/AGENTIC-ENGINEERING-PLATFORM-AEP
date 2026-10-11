from langchain.tools import ToolRuntime
from langchain.tools import tool

@tool
async def search_recent_conversation(query:str, runtime:ToolRuntime) -> str:
    """
        Search the user's previous executions for relevant
        past decisions, implementations, problems, actions,
        or outcomes.

        Use this tool when:
        - the user refers to a previous conversation or decision
        - the task is explicitly a continuation of earlier work
        - important historical context is missing
        - you need to understand how a previous problem was solved
        - the current task needs historical information

        Do not use this tool when:
        - the current context already contains the required information
        - the task is completely independent of previous conversations
    """
    user_id = runtime.context.user_id

    episodic_memory = runtime.context.episodic_memory

    executions = await episodic_memory.search_execution_history(user_id=user_id, query=query, limit=5)

    if not executions:
        return (
            f"No relevant previous execution was found "
            f"for query: {query}"
        )

    historical_results = []

    for row in executions:

        execution_id = row[0]
        thread_id = row[1]
        user_request = row[2]
        messages = row[3]
        created_at = row[4]
        similarity = row[5]

        historical_results.append(
            {
                "execution_id": execution_id,
                "thread_id": thread_id,
                "user_request": user_request,
                "execution_history": messages,
                "created_at": str(created_at),
                "similarity": float(similarity)
            }
        )
    
    return str(
        {
            "query": query,
            "historical_results": historical_results
        }
    )

