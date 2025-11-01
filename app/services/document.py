from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models import Document
from app.schema.document import DocumentCreate, DocumentUpdate  # your Pydantic schemas


class DocumentService:
    @staticmethod
    async def create(db: AsyncSession, document_data: DocumentCreate) -> Document:
        """Create a new document."""
        new_doc = Document(**document_data.model_dump())
        db.add(new_doc)
        await db.commit()
        await db.refresh(new_doc)
        return new_doc

    @staticmethod
    async def get_all(db: AsyncSession) -> list[Document]:
        """Fetch all documents."""
        result = await db.execute(select(Document))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, document_id: int) -> Document:
        """Fetch a single document by ID."""
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {document_id} not found.",
            )
        return document

    @staticmethod
    async def update(
        db: AsyncSession, document_id: int, document_data: DocumentUpdate
    ) -> Document:
        """Update an existing document."""
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {document_id} not found.",
            )

        for key, value in document_data.model_dump(exclude_unset=True).items():
            setattr(document, key, value)

        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document

    @staticmethod
    async def delete(db: AsyncSession, document_id: int) -> None:
        """Delete a document by ID."""
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {document_id} not found.",
            )
        await db.delete(document)
        await db.commit()
