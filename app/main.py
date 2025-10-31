# import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI,UploadFile,File
from app.core.embedding import embbed_model
from app.services.document_parser import DocumentParserService
from app.services.embeddings import EmbeddingService
# from app.core.database import test_connection

@asynccontextmanager
async def lifespan(app:FastAPI):
    embbed_model.init()
    yield
    
app = FastAPI(lifespan=lifespan)

@app.post("/parse")
async def parse_file(file: UploadFile = File(...)):
    try:
        return await DocumentParserService.parse(file)
    except ValueError as e:
        return {"error":str(e)}

@app.post("/embbed")
async def embbed(text:str):
    try:
        return {"embeddings": EmbeddingService.embbed_string(text)}
    except ValueError as e:
        return {"error":str(e)}