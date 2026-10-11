import asyncio

if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )
from uuid import uuid4
from config.embeddings import embeddings
from psycopg_pool import AsyncConnectionPool
from config.database_config import DB_URI 
from psycopg.types.json import Jsonb

async def main():

    user_id = "Varun"
    execution_id = str(uuid4())
    thread_id = str(uuid4())

    user_request = "I was working on the MLflow repository."
    agent = "repository"

    # Generate embedding
    embedding = await embeddings.aembed_query(user_request)

    print("Embedding dimensions:", len(embedding))

    # Connect using the same PostgreSQL DB
    pool = AsyncConnectionPool(
        conninfo=DB_URI,
        open=False
    )

    await pool.open()

    try:
        async with pool.connection() as conn:
            async with conn.cursor() as cursor:

                await cursor.execute(
                    """
                    INSERT INTO episodic_memory_embeddings (
                        user_id,
                        execution_id,
                        thread_id,
                        user_request,
                        agent,
                        messages,
                        artifacts_id,
                        embedding
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        user_id,
                        execution_id,
                        thread_id,
                        user_request,
                        agent,
                        Jsonb({}),
                        Jsonb({}),
                        embedding
                    )
                )

            await conn.commit()

        print("Episodic memory inserted successfully.")
        print("Execution ID:", execution_id)

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())