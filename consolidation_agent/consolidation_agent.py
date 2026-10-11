from langchain.tools import ToolRuntime
from langchain.tools import tool

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

    #checkpoints = [checkpoint async for checkpoint in checkpointer.alist(None)]
    
    if not checkpoints:
        return f"No previous conversation history found for user '{user_id}'."

    # ---------------------------------------------------------
    # 2. Group checkpoints by execution
    # ---------------------------------------------------------

    executions = {}

    for checkpoint in checkpoints:
        execution_id = checkpoint.metadata.get("execution_id")
        if not execution_id:
            continue
        existing = executions.get(execution_id)

        if existing is None:
            executions[execution_id] = checkpoint

        else:
            existing_step = existing.metadata.get("step",-1)
            current_step = checkpoint.metadata.get("step", -1)
            if current_step > existing_step:
                executions[execution_id] = checkpoint

    # ---------------------------------------------------------
    # 3. Inspect latest checkpoint from each historical execution
    # ---------------------------------------------------------
    historical_executions = []

    print("EXECUTIONS:")

    for execution_id, checkpoint in executions.items():

        channel_values = checkpoint.checkpoint.get("channel_values", {})
        print(checkpoint.checkpoint.get("channel_values", {}))

        '''
        print("====================================")
        print("THREAD ID:", checkpoint.config["configurable"]["thread_id"])
        print("CHECKPOINT ID:", checkpoint.config["configurable"].get("checkpoint_id"))
        print("METADATA:", checkpoint.metadata)
        print("====================================")
        print("\nCHECKPOINT KEYS:")
        print(checkpoint.checkpoint.keys())
        print("====================================")
        print("\nCHANNEL VALUES KEYS:")
        print(checkpoint.checkpoint.get("channel_values", {}).keys())
        print("====================================")
        print("\nFULL CHANNEL VALUES:")
        print(checkpoint.checkpoint.get("channel_values", {}))
        print("====================================")
        print("HISTORICAL EXECUTION:", execution_id)
        print("HISTORICAL STEP:", checkpoint.metadata.get("step"))
        print("HISTORICAL TASK:", channel_values.get("user_request"))
        print("====================================")
        '''


        channel_values = checkpoint.checkpoint.get("channel_values", {})
        artifacts_id = channel_values.get("artifacts_id")
        task = channel_values.get("user_request", "")
        agent = channel_values.get("agent", "")
        route_id = channel_values.get("route_id", "")
        messages = channel_values.get("messages", [])

        historical_executions.append(
            {
                "execution_id": execution_id,
                "thread_id": checkpoint.config["configurable"]["thread_id"],
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
            matched_executions.append(execution)

    if not matched_executions:
        return (
            f"No relevant previous execution was found for query: "
            f"{query}"
        )
    
    # ---------------------------------------------------------
    # 5. Fetch actual AgentOutput from Artifact Store
    # ---------------------------------------------------------

    historical_results = []

    for execution in matched_executions:

        artifacts_id = execution["artifacts_id"]
        if not artifacts_id:
            continue

        for agent_name, artifact_id in artifacts_id.items():
            try:
                agent_output = await backend.get_agent_output(user_id,artifact_id)

                if agent_output is None:
                    print(f"Artifact {artifact_id} could not be retrieved.")
                    continue
                historical_results.append(
                    {     
                        "execution_id": execution["execution_id"],
                        "thread_id": execution["thread_id"],
                        "task": execution["task"],
                        "agent": agent_name,
                        "artifact_id": artifact_id,
                        "agent_output": agent_output.model_dump(mode="json"),
                    
                    }
                )
            except Exception as e:

                print(
                f"Failed to retrieve historical artifact "
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

async def checkpoint_extraction(self,user_id, checkpointer, execution_id):
    """ To get latest checkpoint"""

    if checkpointer is None:
        return "Historical conversation search is unavailable: checkpointer is not configured."

    checkpoints  = [checkpoint async for checkpoint in checkpointer.alist(None, filter={"execution_id": execution_id})]

    '''
    for checkpoint in checkpoints:
        channel_values = checkpoint.checkpoint.get("channel_values", {})

        messages = channel_values.get("messages", [])

        print(
            "STEP:", checkpoint.metadata.get("step"),
            "EXECUTION:", checkpoint.metadata.get("execution_id"),
            "MESSAGE COUNT:", len(messages),
            "MESSAGE TYPES:", [type(m).__name__ for m in messages]
        )
    '''    
    if not checkpoints:
        return f"No previous conversation history found for user '{user_id}'."

    # Find latest checkpoints
    latest_checkpoint = max(checkpoints, key = lambda checkpoint:checkpoint.metadata.get("step",-1))

    channel_values = latest_checkpoint.checkpoint.get("channel_values",{})

    messages = channel_values.get("messages", [])

    print("========== SELECTED CHECKPOINT ==========")
    print("STEP:", latest_checkpoint.metadata.get("step"))
    print("MESSAGE COUNT:", len(messages))

    for i, message in enumerate(messages):
        print(i, type(message).__name__, getattr(message, "content", None))
    
    execution_data = {
        "execution_id": execution_id,
        "thread_id": latest_checkpoint.config["configurable"]["thread_id"],
        "user_request": channel_values.get("user_request", ""),
        "messages": channel_values.get("messages", []),
    }

    return execution_data
