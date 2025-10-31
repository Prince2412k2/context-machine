from fastapi import HTTPException, UploadFile
from typing import List
import io 
from bs4 import BeautifulSoup
from docx import Document
from pdfminer.high_level import extract_text
import tempfile
import os
from PIL import Image
import pytesseract
import logging
import io
from pydub import AudioSegment
import httpx
import mimetypes
from app.core.config import settings
import json

logger=logging.getLogger(__name__)



class DocumentParserService:
    @staticmethod
    async def parse(file: UploadFile):
        content_type = file.content_type or ""
        suffix = mimetypes.guess_extension(content_type) or ""
        content = await file.read()
        tmp_path = None

        try:
            # Write file to temp location
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            # Default output values
            output, error, status = "", "", "Success"

            match content_type:
                case "image/png" | "image/jpeg" | "image/webp":
                    output = await ImageParser.parse(tmp_path)
                case "application/pdf":
                    output = await PDFParser.parse(tmp_path)
                case "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    output = await DocxParser.parse(tmp_path)
                case "text/html":
                    output = await HTMLParser.parse(tmp_path)
                case "text/plain" | "text/markdown":
                    output = await TextParser.parse(tmp_path)
                case content_type if content_type in {
                    "audio/flac", "audio/mpeg", "audio/mp3", "audio/m4a",
                    "audio/x-m4a", "audio/ogg", "audio/wav",
                    "audio/x-wav", "audio/webm"
                }:
                    output = await AudioParser.parse(content, content_type)
                case _:
                    status = "Failed"
                    error = f"Unsupported file type: {content_type}"
                    output = ""
        except Exception as e:
            status = "Failed"
            error = str(e)
            output = ""
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

        return {
            "file_name": file.filename,
            "status": status,
            "error": error,
            "text": output
        }
        

    @staticmethod
    async def parse_multiple(files: List[UploadFile]):
        for file in files:
            result= await DocumentParserService.parse(file)
            yield (json.dumps(result) + "\n").encode("utf-8")
        yield json.dumps({
            "file_name": "",
            "status": "Finished",
            "error": "",
            "text": ""
            }).encode("utf-8")


class TextParser:
    @staticmethod
    async def parse(path: str):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return  text


class PDFParser:
    @staticmethod
    async def parse(path: str):
        text = extract_text(path)
        return  text


class DocxParser:
    @staticmethod
    async def parse(path: str):
        doc = Document(path)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text

class HTMLParser:
    @staticmethod
    async def parse(path: str):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)

        return text


class ImageParser:
    @staticmethod
    async def parse(path: str):
        try:
            image=Image.open(path)
            text=pytesseract.image_to_string(image)
            return str(text)
        except Exception as e:
            logger.warning(f"image failed to parse: {e}")

class AudioParser:
    @staticmethod
    async def parse(file:bytes,file_type:str):
        size=len(file)/(1024*1024)
        if size> settings.MAX_AUDIO_SIZE_MB:
            raise HTTPException(status_code=400,detail=f"File too large : file should be less than {settings.MAX_AUDIO_SIZE_MB} MB")
        audio=AudioSegment.from_file(io.BytesIO(file))
        duration_sec = len(audio) / 1000
        duration_min = duration_sec / 60
        if duration_min > settings.MAX_AUDIO_DURATION_MIN:
            raise HTTPException(status_code=400, detail=f"Audio too long: audio should be less than {settings.MAX_AUDIO_DURATION_MIN} min")
        
        ext = mimetypes.guess_extension(file_type) or ".wav"
        async with httpx.AsyncClient(timeout=None) as client:
            form = {"model": "whisper-large-v3-turbo"}
            files = {"file": (f"audio{ext}",file, file_type)}
            headers = {"Authorization": f"Bearer {settings.GROQ_API}"}
            response = await client.post(settings.GROQ_TRANSCRIPTION_URL, data=form, files=files, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()
        return data.get("text")