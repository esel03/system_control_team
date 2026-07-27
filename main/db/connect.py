from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from main.config import settings

DATABASE_URL = settings.get_db_url()


engine = create_async_engine(
    url=DATABASE_URL,
    echo=settings.SQL_ECHO,
    pool_pre_ping=True,
)

async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession,
)


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
