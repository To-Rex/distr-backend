import asyncio
import os
import platform
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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


engine = create_async_engine(DATABASE_URL, pool_size=10, max_overflow=20,
                             pool_pre_ping=True, pool_recycle=3600)
async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def _ensure_alembic_stamp():
    """Stamp the database if alembic_version table has no entry.

    Also handles stale pending migrations: if the head in revision files
    is ahead of the DB stamp but all tables already exist in the DB,
    jump the stamp to head to avoid reapplying create_table ops.
    """
    from config.auto_migration import _create_empty_revision

    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT 1 FROM information_schema.tables WHERE table_name='alembic_version'")
        )
        table_exists = result.scalar() is not None

    if not table_exists:
        async with engine.begin() as conn:
            await conn.execute(text(
                "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) PRIMARY KEY)"
            ))

    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT version_num FROM alembic_version"))
        row = result.fetchone()

    from alembic.config import Config
    from alembic.script import ScriptDirectory
    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    head_rev = script.get_current_head()

    if row:
        if head_rev and row[0] != head_rev:
            async with engine.connect() as conn:
                result = await conn.execute(
                    text("SELECT 1 FROM information_schema.tables WHERE table_name='users'")
                )
                if result.scalar() is not None:
                    async with engine.begin() as conn:
                        await conn.execute(
                            text("UPDATE alembic_version SET version_num=:v"),
                            {"v": head_rev},
                        )
                    print(f"[+] Alembic: jumped to head {head_rev} (tables already exist)")
        return

    # No stamp — create initial revision and stamp with base
    rev = _create_empty_revision()
    if rev is None:
        rev = script.get_base()
        if rev is None:
            rev = script.get_current_head()

    if rev:
        async with engine.begin() as conn:
            await conn.execute(
                text("INSERT INTO alembic_version (version_num) VALUES (:v)"),
                {"v": rev},
            )
        print(f"[+] Alembic: database stamped with revision {rev}")

    # If tables already exist but there are pending migrations, jump to head
    if head_rev and rev != head_rev:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT 1 FROM information_schema.tables WHERE table_name='users'")
            )
            if result.scalar() is not None:
                async with engine.begin() as conn:
                    await conn.execute(
                        text("UPDATE alembic_version SET version_num=:v"),
                        {"v": head_rev},
                    )
                print(f"[+] Alembic: jumped to head {head_rev} (tables already exist)")


async def create_all_tables():
    try:
        await _ensure_alembic_stamp()
        from config.auto_migration import run_auto_migration
        await asyncio.to_thread(run_auto_migration)
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
