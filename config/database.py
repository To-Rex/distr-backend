import os
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.base.models import Base

#DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:toor@distr-distrdb-5ipyhf:5432/mx_soft_db")
DATABASE_URL = "postgresql+asyncpg://postgres:toor@distr-distrdb-5ipyhf:5432/mx_soft_db"
#DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:toor@distr-distrdb-5ipyhf:5432/mx_soft_db")

if os.path.isfile(".env"):
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() == "DATABASE_URL":
                DATABASE_URL = val.strip().strip("\"'")
                break


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
