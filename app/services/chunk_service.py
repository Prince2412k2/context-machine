import re
from typing import List


class ChunkService:
    @staticmethod
    def chunk(doc: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        """
        Splits a long Markdown or plain text into overlapping chunks.

        Args:
            doc: The full text content.
            chunk_size: Max size (in characters) for each chunk.
            overlap: Number of characters of overlap between consecutive chunks.

        Returns:
            A list of text chunks, each ready for embedding.
        """
        # Normalize line breaks and strip redundant whitespace
        text = re.sub(r"\s+", " ", doc.strip())

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + chunk_size, text_length)

            # Try not to cut words in half — move end back to nearest space or punctuation
            if end < text_length:
                nearest_space = text.rfind(" ", start, end)
                if nearest_space > start + chunk_size * 0.6:  # don't move too far back
                    end = nearest_space

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = max(end - overlap, end)  # maintain overlap but avoid infinite loop

        return chunks
