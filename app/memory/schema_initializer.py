
from psycopg_pool import AsyncConnectionPool

async def initialize_episodic_schema(db_pool: AsyncConnectionPool) -> None:
    """Initialize AEP episodic memory schema if it does not exist."""

    async with db_pool.connection() as conn:
        async with conn.cursor() as cur:

            # 1. Enable pgvector
            await cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

            
            # 2. To store the user trace 
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memory_embeddings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id TEXT NOT NULL,
                    execution_id TEXT NOT NULL,
                    thread_id TEXT NOT NULL,
                    user_request TEXT,
                    agent TEXT,
                    messages JSONB,
                    artifacts_id JSONB,
                    created_at TIMESTAMP(0) NOT NULL DEFAULT NOW(),
                    embedding VECTOR(1536),
                    CONSTRAINT unique_execution_id UNIQUE (execution_id)
                )
            """)

            # 2. Store completed execution history and embeddings
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memory_embeddings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id TEXT NOT NULL,
                    execution_id TEXT NOT NULL,
                    thread_id TEXT NOT NULL,
                    user_request TEXT,
                    agent TEXT,
                    messages JSONB,
                    artifacts_id JSONB,
                    created_at TIMESTAMP(0) NOT NULL DEFAULT NOW(),
                    embedding VECTOR(1536),
                    CONSTRAINT unique_execution_id UNIQUE (execution_id)
                )
            """)

            # 3. Store executions that are still in progress
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS episodic_execution_in_progress (
                    execution_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    thread_id TEXT NOT NULL,
                    user_request TEXT,
                    messages JSONB NOT NULL DEFAULT '[]'::jsonb,
                    updated_at TIMESTAMP(0) NOT NULL DEFAULT NOW()
                )
            """)

            # 4. Vector similarity index
            await cur.execute("""
                CREATE INDEX IF NOT EXISTS episodic_memory_embedding_idx
                ON episodic_memory_embeddings
                USING hnsw (embedding vector_cosine_ops)
            """)

            # 5. User lookup index
            await cur.execute("""
                CREATE INDEX IF NOT EXISTS episodic_memory_user_id_idx
                ON episodic_memory_embeddings (user_id)
            """)

        await conn.commit()
