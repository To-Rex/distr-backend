import os
import platform
from collections.abc import AsyncGenerator
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.base.models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "") or "postgresql+asyncpg://localhost:5432/postgres"

# Only install PostgreSQL client on Linux (not macOS)
if platform.system() == "Linux":
    os.system("""
        apt update -qq && apt install -y curl ca-certificates gnupg lsb-release &&
        curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
            | gpg --dearmor -o /usr/share/keyrings/postgresql.gpg &&
        echo "deb [signed-by=/usr/share/keyrings/postgresql.gpg] \
            https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
            > /etc/apt/sources.list.d/pgdg.list &&
        apt update -qq &&
        apt install -y postgresql-client-18
    """)


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession)

_pg_dialect = postgresql.dialect()


def _compile_col_type(column: Any) -> str:
    return column.type.compile(dialect=_pg_dialect)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def create_all_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        for table_name, table in Base.metadata.tables.items():
            for column in table.columns:
                try:
                    col_type = _compile_col_type(column)
                    await conn.execute(text(
                        f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column.name} {col_type} NULL"
                    ))
                except Exception:
                    pass


async def check_db_alive() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def dispose_engine():
    await engine.dispose()
