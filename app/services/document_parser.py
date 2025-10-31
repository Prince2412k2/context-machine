from fastapi import HTTPException, UploadFile
from typing import List
from io import BytesIO
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

logger=logging.getLogger(__name__)

class DocumentParserService:
    @staticmethod
    async def parse(file: UploadFile):
        content_type = file.content_type
        suffix = os.path.splitext(file.filename)[-1]
        content=await file.read()
        # Write uploaded file to a temporary file for parsing
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            match content_type:
                case "image/png" | "image/jpeg" | "image/webp":
                    result = await ImageParser.parse(tmp_path)
                case "application/pdf":
                    result = await PDFParser.parse(tmp_path)
                case "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    result = await DocxParser.parse(tmp_path)
                case "text/html":
                    result = await HTMLParser.parse(tmp_path)
                case "text/plain" | "text/markdown":
                    result = await TextParser.parse(tmp_path)
                case  "audio/flac" | "audio/mpeg"| "audio/mp3"|"audio/m4a"|"audio/x-m4a"|"audio/ogg"|"audio/wav"|"audio/x-wav"|"audio/webm":
                    result = await AudioParser.parse(content,content_type)
                case _:
                    raise ValueError(f"Unsupported file type: {content_type}")
        finally:
            os.remove(tmp_path)

        return result

    @staticmethod
    async def parse_multiple(files: List[UploadFile]):
        results = []
        for file in files:
            results.append(await DocumentParserService.parse(file))
        return results


class TextParser:
    @staticmethod
    async def parse(path: str):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return {"text": text, "images": []}


class PDFParser:
    @staticmethod
    async def parse(path: str):
        text = extract_text(path)
        return {"text": text, "images": []}


class DocxParser:
    @staticmethod
    async def parse(path: str):
        doc = Document(path)
        text = "\n".join([p.text for p in doc.paragraphs])
        return {"text": text, "images": []}


class HTMLParser:
    @staticmethod
    async def parse(path: str):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        images = [img.get("src") for img in soup.find_all("img") if img.get("src")]
        return {"text": text, "images": images}


class ImageParser:
    @staticmethod
    async def parse(path: str):
        try:
            image=Image.open(path)
            text=pytesseract.image_to_string(image)
            return {"image":str(text)} 
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
        return {
            "text": data.get("text"),
            "duration_min": round(duration_min, 2),
            "language": data.get("language", "unknown")
        }