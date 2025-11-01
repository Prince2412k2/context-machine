from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(BigInteger, primary_key=True, index=True)
    owner_id = Column(BigInteger, index=True, nullable=True)
    title = Column(String, nullable=True)

    chunks = relationship(
        "Chunk", back_populates="document", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True)
    document_id = Column(
        BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    owner_id = Column(BigInteger, index=True, nullable=True)
    chunk_index = Column(Integer, nullable=True)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(384))  # Adjust to your embedding dimension

    document = relationship("Document", back_populates="chunks")
    __table_args__ = (Index("idx_chunks_document_id", "document_id"),)
