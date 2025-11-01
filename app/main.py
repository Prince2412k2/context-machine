# import asyncio
from contextlib import asynccontextmanager
from typing import List
from fastapi import Depends, FastAPI, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.embedding import embbed_model
from app.schema.document import DocumentCreate
from app.services.chunk_service import ChunkService
from app.services.document import DocumentService
from app.services.document_parser import DocumentParserService
from app.services.embeddings import EmbeddingService, VectorService
from app.core.database import init_db
# from app.core.database import test_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    embbed_model.init()
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/parse")
async def parse_file(file: UploadFile = File(...)):
    try:
        return await DocumentParserService.parse(file)
    except ValueError as e:
        return {"error": str(e)}


@app.post("/embbed")
async def embbed(text: str):
    try:
        return {"embeddings": EmbeddingService.embbed_string(text)}
    except ValueError as e:
        return {"error": str(e)}


@app.post("/save")
async def save(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    document = await DocumentService.create(
        db,
        document_data=DocumentCreate(title=file.filename or "None"),
    )
    result = await DocumentParserService.parse(file)
    chunks = ChunkService.chunk(result["text"])
    embeddings = EmbeddingService.embbed_doc(chunks)

    await VectorService.upsert_chunks(
        db,
        document_id=document.id,
        owner_id=12312415353,
        chunks=(chunks),
        embeddings=embeddings,
    )
    return {"msg": "success"}


class QuerySchema(BaseModel):
    query: str
    doc_ids: List[int]


@app.post("/query")
async def query(query: QuerySchema, db: AsyncSession = Depends(get_db)):
    embeddings = EmbeddingService.embbed_string(query.query)
    output = await VectorService.query_similar_chunks(
        db,
        query_embedding=embeddings,
        document_ids=query.doc_ids,
    )
    return {"success": output}
