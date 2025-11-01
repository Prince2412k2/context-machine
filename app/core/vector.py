import qdrant_client
import asyncio
from app.core.config import settings


class QdrantClient:
    _instance = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        self.client = None

    def init(self):
        if self.client is None:
            self.client = qdrant_client.AsyncQdrantClient(
                settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY
            )

    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance.model = QdrantClient()  # pyright: ignore
                    cls._instance = instance
        return cls._instance


qdrant = QdrantClient()


def get_qdrant() -> qdrant_client.AsyncQdrantClient:
    if qdrant.client is None:
        raise ValueError("Qdrant Client not initialized")
    return qdrant.client
