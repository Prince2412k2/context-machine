from typing import List
from fastapi import UploadFile


class FileService:

    @staticmethod
    async def process_files(files:List[UploadFile]):
        """
        iterate through files. 
        1.  parse them.
        2.  embed them
        3.  save file to db and bucket
        4.  save embeddings to db
        """
        pass