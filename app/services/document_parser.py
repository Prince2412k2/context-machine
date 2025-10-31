from fastapi import UploadFile
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
logger=logging.getLogger(__name__)

class DocumentParserService:
    @staticmethod
    async def parse(file: UploadFile):
        content_type = file.content_type
        suffix = os.path.splitext(file.filename)[-1]
        
        # Write uploaded file to a temporary file for parsing
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
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