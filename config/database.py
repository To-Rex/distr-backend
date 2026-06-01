import os
import platform
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "") or "postgresql+asyncpg://localhost:5432/postgres"

# Only install PostgreSQL client on Linux if not already present
if platform.system() == "Linux" and os.system("which psql >/dev/null 2>&1") != 0:
    os.system(
        "apt update -qq && apt install -y -qq curl ca-certificates gnupg lsb-release "
        "&& curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc "
        "| gpg --batch --dearmor -o /usr/share/keyrings/postgresql.gpg 2>/dev/null "
        '&& echo "deb [signed-by=/usr/share/keyrings/postgresql.gpg] '
        "https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main\" "
        "> /etc/apt/sources.list.d/pgdg.list "
        "&& apt update -qq && apt install -y -qq postgresql-client-18"
    )


engine = create_async_engine(DATABASE_URL, pool_size=10, max_overflow=20,
                             pool_pre_ping=True, pool_recycle=3600)
async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def create_all_tables():
    from apps.base.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_db_alive() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def dispose_engine():
    await engine.dispose()
