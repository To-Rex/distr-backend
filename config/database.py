import asyncio
import atexit
import os
import platform
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

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

    from config.auto_migration import _make_alembic_config
    cfg = _make_alembic_config()
    if cfg is None:
        print("[!] Alembic: cannot stamp — config unavailable")
        return
    from alembic.script import ScriptDirectory
    try:
        script = ScriptDirectory.from_config(cfg)
    except Exception as e:
        print(f"[!] Alembic: cannot create ScriptDirectory — {e}")
        return
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


async def _sync_missing_columns():
    """Add any columns defined in ORM models that are missing from actual DB tables.

    This is a fallback for when Alembic autogenerate fails or is unavailable.
    Only handles simple column types (no foreign keys, no enums — those are
    assumed to already exist or be created by create_all).
    """
    import sqlalchemy as sa
    from apps.base.models import Base

    for table_name, table in Base.metadata.tables.items():
        try:
            async with engine.connect() as conn:
                result = await conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = :t"
                    ),
                    {"t": table_name},
                )
                existing_cols = {row[0] for row in result}
        except Exception as e:
            print(f"[!] Column sync: could not read columns for {table_name} — {e}")
            continue

        for col in table.columns:
            if col.name in existing_cols:
                continue

            col_type = col.type

            if isinstance(col_type, sa.Enum):
                continue

            if isinstance(col_type, sa.Integer):
                raw_type = "INTEGER"
            elif isinstance(col_type, sa.String):
                raw_type = f"VARCHAR({col_type.length or 255})"
            elif isinstance(col_type, sa.DateTime):
                raw_type = "TIMESTAMP WITHOUT TIME ZONE"
            elif isinstance(col_type, sa.Boolean):
                raw_type = "BOOLEAN"
            elif isinstance(col_type, sa.Text):
                raw_type = "TEXT"
            elif isinstance(col_type, sa.Float):
                raw_type = "FLOAT"
            elif isinstance(col_type, sa.Numeric):
                raw_type = "NUMERIC"
            else:
                print(f"[!] Column sync: unsupported type {type(col_type).__name__} for {table_name}.{col.name}, skipping")
                continue

            nullable_sql = "NULL" if col.nullable else "NOT NULL"

            alter_sql = f'ALTER TABLE "{table_name}" ADD COLUMN "{col.name}" {raw_type} {nullable_sql}'
            try:
                async with engine.begin() as conn:
                    await conn.execute(text(alter_sql))
                print(f"[+] Column sync: added {table_name}.{col.name} ({raw_type})")
            except Exception as e:
                print(f"[!] Column sync: failed to add {table_name}.{col.name} — {e}")


_migration_done = False
_MIGRATION_LOCK = Path(tempfile.gettempdir()) / "mxsoft_migration.lock"


def _migration_lock_valid() -> bool:
    if not _MIGRATION_LOCK.exists():
        return False
    try:
        pid = int(_MIGRATION_LOCK.read_text().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        _MIGRATION_LOCK.unlink(missing_ok=True)
        return False

async def create_all_tables(force: bool = False):
    global _migration_done

    # Always create/update tables from ORM models (create missing tables,
    # but does NOT add columns to existing tables — that's handled below).
    from apps.base.models import Base
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"[!] Base.metadata.create_all failed: {e}")

    if not force and (_migration_done or _migration_lock_valid()):
        if _migration_done:
            print("[i] Alembic: migration already applied, skipping")
        elif _migration_lock_valid():
            print("[i] Alembic: migration already applied (lock file), skipping")
        _migration_done = True
    else:
        try:
            await _ensure_alembic_stamp()
            from config.auto_migration import run_auto_migration
            await asyncio.to_thread(run_auto_migration)
        except Exception as e:
            print(f"[!] Alembic auto_migration failed: {e}")

        _migration_done = True
        _MIGRATION_LOCK.touch()
        _MIGRATION_LOCK.write_text(f"{os.getpid()}")

    # Column sync runs on every startup (not gated by migration lock)
    # to ensure ORM columns exist even when auto_migration is skipped.
    try:
        await _sync_missing_columns()
    except Exception as e:
        print(f"[!] Column sync failed: {e}")

async def check_db_alive() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

async def dispose_engine():
    await engine.dispose()
