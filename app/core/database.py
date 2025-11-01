from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models import Base, Document, Chunk

from sqlalchemy import text as sql_text


engine = create_async_engine(
    settings.DB_URL,
    echo=True,
    future=True,
)

AsyncSessionLocal: sessionmaker[AsyncSession] = sessionmaker(  # type: ignore
    engine,  # type: ignore
    expire_on_commit=False,
    class_=AsyncSession,
)  # type: ignore


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_vector_schema(conn: AsyncConnection):
    """Ensure pgvector extension and create tables."""
    await conn.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector;"))
    await conn.run_sync(Base.metadata.create_all)


async def create_hnsw_index(
    conn: AsyncConnection, m: int = 16, ef_construction: int = 64
):
    """Create a HNSW index for fast ANN search (cosine distance)."""
    await conn.execute(
        sql_text(
            "CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw "
            "ON chunks USING hnsw (embedding vector_cosine_ops) "
            f"WITH (m = {m}, ef_construction = {ef_construction});"
        )
    )


async def init_db():
    async with engine.begin() as conn:
        # 1. Make sure pgvector is available
        await conn.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector;"))

        # 2. Create all ORM tables
        await conn.run_sync(Base.metadata.create_all)

    # 3. Open a new connection (after tables exist) to create the index
    async with engine.begin() as conn:
        await conn.execute(
            sql_text(
                "CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw "
                "ON chunks USING hnsw (embedding vector_cosine_ops) "
                "WITH (m = 16, ef_construction = 64);"
            )
        )
