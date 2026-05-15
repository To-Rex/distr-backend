from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.base.models import Base

DATABASE_URL = "postgresql://postgres:toor@postgres:5432/mx_soft_db"
#DATABASE_URL = "postgresql+asyncpg://postgres:toor@localhost:5432/mx_soft_db"
#DATABASE_URL = "postgresql+asyncpg://torex@localhost:5432/mx_soft_db"


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def create_all_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
