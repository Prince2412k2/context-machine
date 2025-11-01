from fastembed.common.types import NumpyArray
from app.core.embedding import get_embbed
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Chunk
import numpy as np

##
from sqlalchemy import (
    text as sql_text,
)

from typing import Iterable, List, Optional
from uuid import uuid4
from sqlalchemy.dialects.postgresql import insert as pg_insert

##


class EmbeddingService:
    @staticmethod
    def embbed_doc(chunks: List[str]):
        """returns Vectors of 384 dimensions"""
        return get_embbed().embed(chunks)

    @staticmethod
    def embbed_string(query: str):
        return list(get_embbed().embed([query]))[0]


class VectorService:
    @staticmethod
    async def upsert_chunks(
        session: AsyncSession,
        document_id: int,
        owner_id: Optional[int],
        chunks: List[str],
        embeddings: Iterable[NumpyArray],
    ):
        """Bulk upsert text chunks and embeddings into the database."""
        records = [
            {
                "id": str(uuid4()),
                "document_id": document_id,
                "owner_id": owner_id,
                "chunk_index": i,
                "text": text,
                "embedding": emb.tolist(),
            }
            for i, (text, emb) in enumerate(zip(chunks, embeddings))
        ]

        stmt = pg_insert(Chunk.__table__).values(records)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "text": stmt.excluded.text,
                "embedding": stmt.excluded.embedding,
                "chunk_index": stmt.excluded.chunk_index,
                "owner_id": stmt.excluded.owner_id,
            },
        )

        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def delete_chunks_by_document(session: AsyncSession, document_id: int):
        """Delete all chunks for a given document."""
        await session.execute(
            Chunk.__table__.delete().where(Chunk.document_id == document_id)
        )
        await session.commit()

    @staticmethod
    async def query_similar_chunks(
        session: AsyncSession,
        query_embedding: NumpyArray,
        top_k: int = 5,
        owner_id: Optional[int] = None,
        document_ids: Optional[List[int]] = None,
    ):
        """Find similar chunks using pgvector's <=> cosine distance operator."""
        params = {"qvec": str(query_embedding.tolist()), "limit": top_k}

        where_clauses = []
        if owner_id is not None:
            where_clauses.append("owner_id = :owner_id")
            params["owner_id"] = owner_id
        if document_ids:
            where_clauses.append("document_id = ANY(:doc_ids)")
            params["doc_ids"] = document_ids

        where_sql = " AND ".join(where_clauses) if where_clauses else "TRUE"

        sql = sql_text(f"""
            SELECT
                id,
                document_id,
                text,
                embedding <=> (:qvec)::vector AS distance
            FROM chunks
            WHERE {where_sql}
            ORDER BY embedding <=> (:qvec)::vector
            LIMIT :limit
        """)

        result = await session.execute(sql, params)
        rows = result.fetchall()
        return [
            {
                "id": r.id,
                "document_id": r.document_id,
                "text": r.text,
                "distance": float(r.distance),
            }
            for r in rows
        ]

    @staticmethod
    async def query_similar_documents(
        session: AsyncSession,
        query_embedding: NumpyArray,
        owner_id: Optional[int] = None,
        candidate_document_ids: Optional[List[int]] = None,
        top_k_docs: int = 5,
        chunks_to_consider: int = 200,
    ):
        """Aggregate chunk similarity to rank documents."""
        params = {
            "qvec": query_embedding.tolist(),
            "limit_chunks": chunks_to_consider,
            "top_k_docs": top_k_docs,
        }
        where = []

        if owner_id is not None:
            where.append("c.owner_id = :owner_id")
            params["owner_id"] = owner_id
        if candidate_document_ids:
            where.append("c.document_id = ANY(:candidate_document_ids)")
            params["candidate_document_ids"] = candidate_document_ids

        where_sql = " AND ".join(where) if where else "TRUE"

        sql = sql_text(f"""
            WITH top_chunks AS (
                SELECT
                    c.id,
                    c.document_id,
                    c.embedding <=> (:qvec)::vector AS distance
                FROM chunks c
                WHERE {where_sql}
                ORDER BY c.embedding <=> (:qvec)::vector
                LIMIT :limit_chunks
            )
            SELECT
                tc.document_id,
                COUNT(*) AS match_count,
                AVG(1 - tc.distance) AS avg_similarity
            FROM top_chunks tc
            GROUP BY tc.document_id
            ORDER BY avg_similarity DESC
            LIMIT :top_k_docs;
        """)

        result = await session.execute(sql, params)
        rows = result.fetchall()
        return [
            {
                "document_id": r.document_id,
                "match_count": int(r.match_count),
                "avg_similarity": float(r.avg_similarity),
            }
            for r in rows
        ]
