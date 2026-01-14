from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from main.config import settings
from typing import AsyncGenerator


DATABASE_URL = settings.get_db_url()


engine = create_async_engine(url=DATABASE_URL, echo=True)

async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_maker() as session:
        yield session
