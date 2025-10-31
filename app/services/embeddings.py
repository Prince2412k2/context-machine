from typing import List
from app.core.embedding import get_embbed
from sqlalchemy.ext.asyncio import AsyncSession

class EmbeddingService:
    @staticmethod
    def embbed_doc(chunks:List[str]):
        """ returns Vectors of 384 dimensions """
        return get_embbed().embed(chunks)
    
    @staticmethod
    def embbed_string(query:str):
        return list(get_embbed().embed([query]))[0].tolist()

class QueryService:
    
    @staticmethod
    def query(query:str,user_id:str,db:AsyncSession,documents:List[int]):
        embed_query=EmbeddingService.embbed_string(query)
        #TODO : search for result in documents
        pass