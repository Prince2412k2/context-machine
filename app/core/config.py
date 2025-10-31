from typing import ClassVar
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
        DB_URL:str
        GROQ_API:str
        GROQ_TRANSCRIPTION_URL:ClassVar[str] = "https://api.groq.com/openai/v1/audio/transcriptions"
        MAX_AUDIO_SIZE_MB :ClassVar[int]= 10      
        MAX_AUDIO_DURATION_MIN :ClassVar[int]= 20  
            
        class Config:
            env_file = ".env"
settings=Settings()