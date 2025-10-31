from typing import List
from app.core.embedding import embed_model
from sqlalchemy.ext.asyncio import AsyncSession

class EmbeddingService:
    @staticmethod
    def embbed_doc(chunks:List[str]):
        """ returns Vectors of 384 dimensions """
        return embed_model.embed(chunks)
    
    @staticmethod
    def embbed_string(query:str):
        return list(embed_model.embed([query]))[0]

class QueryService:
    
    @staticmethod
    def query(query:str,user_id:str,db:AsyncSession,documents:List[int]):
        embed_query=EmbeddingService.embbed_string(query)
        #TODO : search for result in documents
        pass