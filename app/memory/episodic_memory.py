from config.embeddings import embeddings
from psycopg.types.json import Jsonb
from logger.log import setup_logging
log = setup_logging()

class EpisodicMemory:

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.execution_histories = {}


    def normalize_message(self,messages):
        normalized = []
        for message in messages:
            message_type = message.__class__.__name__

            # Human Message
            if message_type == "HumanMessage":
                normalized.append(f"Router_Request: {message.content}")

            # AI Message
            elif message_type == "AIMessage":
                content = message.content
                text_parts = []

                if isinstance(content, list):

                    for block in content:

                        # Process dictionaries only
                        if not isinstance(block, dict):
                            continue

                        block_type = block.get("type")

                        # Exclude reasoning blokcs
                        if block_type == "reasoning":
                            continue 

                        # Preserve function/tool calls
                        if block_type == 'function_call':
                            tool_name = block.get("name","unkown")
                            arguments = block.get("arguments","")

                            text_parts.append(
                                            f"Tool_called_by_LLM : {tool_name}\n"
                                            f"Arguments_passed_by_LLM_to_tool:{arguments}"
                            )

                        # Preserve ordinary text output
                        elif block_type == "text":
                            value = block.get("text", "")
                            if value:
                                text_parts.append(value)

                elif isinstance(content, str):
                    text_parts.append(content)

                final_content = "\n".join(text_parts).strip()

                if final_content:
                    normalized.append(f"Action taken by llm to router task : {final_content}")

                # Preserve tool-call names when available
                tool_calls = getattr(message, "tool_calls", None)

                if tool_calls:
                    tool_names = [tool_call.get("name","unknown") for tool_call in tool_calls]
                    log.info("Tool_names_called%s",tool_names)
                    normalized.append(f"Tools Called: {', '.join(tool_names)}")

            # Tool result
            elif message_type == "ToolMessage":
                tool_name = getattr(message,"name","")
                tool_message = ""
                if message.status == 'success':
                    tool_message = (f"Tool_Execution_status -> 'success' ")
    
                    #content = message.content
                    #tool_message = ""
                    #if isinstance(content,list):
                        #text_parts = [block['text'] for block in content if isinstance(block,dict) and block.get("type") == 'text' and block.get("text")]
                        #tool_message = "\n".join(text_parts)
            
                    #elif isinstance(content, str):
                        #tool_message = content

                elif message.status == 'error':
                    content = message.content
                    if isinstance(content,list):
                        text_parts = [block['text'] for block in content if isinstance(block,dict) and block.get("type") == 'text' and block.get("text")]
                        tool_message = "\n".join(text_parts)

                    elif isinstance(content, str):
                        tool_message = ("Tool_Execution_status -> 'error'\n"
                                        f"Failure_reason -> {content}")

                normalized.append("Tool result -> %s" % tool_message.strip())

            else:
                normalized.append(f"{message_type}: {message.content}")
     
        return "\n\n".join(normalized)

    async def add_execution_history(self,execution_id: str, messages, user_request:str, thread_id:str, user_id: str):

        normalized = self.normalize_message(messages)

        #log.info("Normalized_message:%s",normalized)


        if execution_id not in self.execution_histories:
            self.execution_histories[execution_id] = {
            "execution_id": execution_id,
            "thread_id": thread_id,
            "user_request": user_request,
            "messages": []
        }


        self.execution_histories[execution_id]["messages"].append(normalized)

        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    INSERT INTO episodic_execution_in_progress (
                        execution_id,
                        user_id,
                        thread_id,
                        user_request,
                        messages,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (execution_id)
                    DO UPDATE SET
                        messages = episodic_execution_in_progress.messages || EXCLUDED.messages,
                        updated_at = NOW()
                    """,
                    # EXCLUDED.messages means the messages value that the new insert attempted to add but couldn't because of the conflict.
                    (
                        execution_id,
                        user_id,
                        thread_id,
                        user_request,
                        Jsonb([normalized])
                    )
                )
            await conn.commit()

  
    def get_execution_history(self,execution_id:str):
        return self.execution_histories.get(execution_id)

        
    async def recover_execution_history(self, execution_id: str):
        """ Read the data from Temporary table"""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT
                        execution_id,
                        user_id,
                        thread_id,
                        user_request,
                        messages
                    FROM episodic_execution_in_progress
                    WHERE execution_id = %s
                    """,
                    (execution_id,)
                )

                row = await cursor.fetchone() 

                ''' 
                Python receives these values as a tuple, approximately: row = (
                                            "EXEC-101",
                                            "Chetan",
                                            "THREAD-01",
                                            "Analyze my repository",
                                            ["Listed files", "Read README"]
                                            ) 
                '''

        if not row:
            return None

        # converts the tuple into a dictionary with meaningful field names.
        return {
            "execution_id": row[0],
            "user_id": row[1],
            "thread_id": row[2],
            "user_request": row[3],
            "messages": row[4]
        }

                 
    async def store_execution(self, execution_data: dict, user_id: str):
        """ Store history in table with embedidng"""

        user_request = execution_data.get("user_request", "")

        execution_history = "\n\n".join(execution_data.get("messages", []))

        embedding_text = f"""
                            User request:
                            {user_request}

                            Execution history:
                            {execution_history}""".strip()
        
        embedding = await embeddings.aembed_query(embedding_text)

        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:

                await cursor.execute(
                    """
                    INSERT INTO episodic_memory_embeddings (
                        user_id,
                        execution_id,
                        thread_id,
                        user_request,
                        messages,
                        embedding
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (execution_id) DO NOTHING
                    """,
                    (
                        user_id,
                        execution_data["execution_id"],
                        execution_data["thread_id"],
                        user_request,
                        Jsonb(execution_data.get("messages", [])),
                        embedding
                    )
                )

            await conn.commit()
            

    async def delete_in_progress_history(self, execution_id: str):
        """ Deleting Temporary Table"""
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    DELETE FROM episodic_execution_in_progress
                    WHERE execution_id = %s
                    """,
                    (execution_id,)
                )
            await conn.commit()



    async def search_execution_history(self, user_id: str, query: str, limit: int = 5):
        """ Search the Table"""
        query_embedding = await embeddings.aembed_query(query)
        async with self.db_pool.connection() as conn:
            async with conn.cursor() as cursor:

                await cursor.execute(
                    """
                    SELECT
                        execution_id,
                        thread_id,
                        user_request,
                        messages,
                        created_at,
                        1 - (embedding <=> %s::vector) AS similarity
                    FROM episodic_memory_embeddings
                    WHERE user_id = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (
                        query_embedding,
                        user_id,
                        query_embedding,
                        limit
                    )
                )

                rows = await cursor.fetchall()

        return rows

