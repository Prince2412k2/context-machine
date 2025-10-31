# import asyncio
# from contextlib import asynccontextmanager
from fastapi import FastAPI,UploadFile,File
from app.services.document_parser import DocumentParserService
# from app.core.database import test_connection

# @asynccontextmanager
# async def lifespan(app:FastAPI):
#     await test_connection()
    # yield
    
# app = FastAPI(lifespan=lifespan)
app = FastAPI()

@app.post("/parse")
async def parse_file(file: UploadFile = File(...)):
    try:
        return await DocumentParserService.parse(file)
    except ValueError as e:
        return {"error":str(e)}