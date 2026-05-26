import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.base.models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL","")
os.system("apt update && apt install -y postgresql-client")

#if not DATABASE_URL:
    #DATABASE_URL = "postgresql+asyncpg://postgres:toor@distr.mxsoft.uz:5432/mx_soft_db"


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def create_all_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_engine():
    await engine.dispose()
