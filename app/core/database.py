from sqlalchemy.ext.asyncio import AsyncSession,create_async_engine
from sqlalchemy.orm import sessionmaker,declarative_base
from app.core.config import settings

Base=declarative_base()

engine=create_async_engine(settings.DB_URL,echo=True,future=True,)

AsyncSessionLocal: sessionmaker[AsyncSession] = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)# type: ignore

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
        
