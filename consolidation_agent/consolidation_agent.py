from langchain.tools import ToolRuntime
from langchain.tools import tool
from app.backends.store.store import backend 
     

@tool
async def search_recent_conversation(query:str, runtime:ToolRuntime) -> str:
    """   
        Search the user's previous conversations for relevant past decisions, implementations, problems, or outcomes.

        Use this tool when:
        - the user refers to a previous conversation or decision
        - the task is explicitly a continuation of earlier work
        - important historical context is missing from the current context
        - you need to understand why a previous architectural decision was made
        - Current task needs historical information

        Do not use this tool when:
        - the current context already contains the required information
        - the task is completely independent of previous conversations
    """
    user_id = runtime.context.user_id
    checkpointer = runtime.context.checkpointer
    backend = runtime.context.backend


    if checkpointer is None:
           return "Historical conversation search is unavailable: checkpointer is not configured."

    # ---------------------------------------------------------
    # 1. Get all checkpoints belonging to this user
    # ---------------------------------------------------------

    checkpoints  = [checkpoint async for checkpoint in checkpointer.alist(None, filter={"user_id": user_id})]

    if not checkpoints:
            return f"No previous conversation history found for user '{user_id}'."

    # ---------------------------------------------------------
    # 2. Group checkpoints by thread
    # ---------------------------------------------------------

    threads = {}

    for checkpoint in checkpoints:
        thread_id = checkpoint.config["configurable"]['thread_id']
        existing = threads.get(thread_id)

        if existing is None:
              threads[thread_id] = checkpoint

        else:
            existing_step = existing.metadata.get("step",-1)
            current_step = checkpoint.metadata.get("step", -1)
            if current_step > existing_step:
                threads[thread_id] = checkpoint

    # ---------------------------------------------------------
    # 3. Inspect latest checkpoint from each historical thread
    # ---------------------------------------------------------
    historical_executions = []

    for thread_id, checkpoint in threads.items():
        channel_values = checkpoint.checkpoint.get("channel_values",{})
        artifacts_id = channel_values.get("artifacts_id")
        task = channel_values.get("task","")
        agent = channel_values.get("agent","")
        route_id = channel_values.get("route_id","")
        messages = channel_values.get("messages",[])

        historical_executions.append(
            {
                "thread_id": thread_id,
                "step": checkpoint.metadata.get("step"),
                "task": task,
                "agent": agent,
                "route_id": route_id,
                "messages": messages,
                "artifacts_id": artifacts_id,
            }
        )


    # ---------------------------------------------------------
    # 4. Simple relevance matching
    # ---------------------------------------------------------
    #
    # First version intentionally uses keyword matching.
    # We can replace this later with semantic retrieval.
    
    query_words  = {word.lower() for word in query.split() if len(word) > 2}

    matched_executions = []

    for execution in historical_executions:
        
        searchable_text = " ".join(
            [ 
                str(execution["task"]),
                str(execution["agent"]),
                str(execution["route_id"]),
                str(execution["messages"]),
            ]).lower()

        matched_words = [word for word in query_words if word in searchable_text]

        if matched_words:
            execution["matched_words"] = matched_words
            matched_executions.append(execution)

    if not matched_executions:
        return (
            f"No relevant previous execution was found for query: "
            f"{query}"
        )
    
    # ---------------------------------------------------------
    # 5. Fetch actual AgentOutput from Artifact Store
    # ------

    historical_results = []
    for execution in matched_executions:
        artifacts_id = execution["artifacts_id"]
        if not artifacts_id:
            continue

        for agent_name,artifact_id in artifacts_id.items():
            try:
                agent_output = backend.get_agent_output(user_id,artifact_id)
                historical_results.append(
                    {
                        "thread_id": execution["thread_id"],
                        "task": execution["task"],
                        "agent": agent_name,
                        "artifact_id": artifact_id,
                        "agent_output": agent_output.model_dump(mode="json"),
                    
                    }
                )
            except Exception as e:

                print(
                f"⚠️ Failed to retrieve historical artifact "
                f"{artifact_id}: {e}"
            )
                continue

    # ---------------------------------------------------------
    # 6. Return actual historical information
    # ---------------------------------------------------------

    if not historical_results:
        return (
            f"Relevant historical executions were found for "
            f"query '{query}', but no AgentOutput could be retrieved."
        )

    return str(
        {
            "query": query,
            "historical_results": historical_results,
        }
    )
                  

         
