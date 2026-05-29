import os
import asyncpg
from urllib.parse import urlparse, unquote

import config.database as _db


def _parse_db_url(url: str) -> dict:
    if not url:
        return {}
    try:
        cleaned = url.replace("postgresql+asyncpg://", "postgresql://")
        parsed = urlparse(cleaned)
        return {
            "host": parsed.hostname or "localhost",
            "port": str(parsed.port or 5432),
            "user": unquote(parsed.username or "postgres"),
            "password": unquote(parsed.password or ""),
            "database": (parsed.path or "/postgres").lstrip("/"),
        }
    except Exception:
        return {}


async def test_connection(
    host: str, port: int, user: str, password: str, database: str
) -> tuple[bool, str | None]:
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            timeout=10,
        )
        await conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def build_db_url(host: str, port: int, user: str, password: str, database: str) -> str:
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"


def save_db_url(host: str, port: int, user: str, password: str, database: str) -> str:
    db_url = build_db_url(host, port, user, password, database)
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
    )

    lines: list[str] = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()

    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith("DATABASE_URL"):
            lines[i] = f"DATABASE_URL={db_url}\n"
            found = True
            break

    if not found:
        lines.append(f"DATABASE_URL={db_url}\n")

    with open(env_path, "w") as f:
        f.writelines(lines)

    return db_url


def get_current_db_params() -> dict:
    url = os.getenv("DATABASE_URL", "") or _db.DATABASE_URL
    return _parse_db_url(url)


async def apply_and_reconnect(
    host: str, port: int, user: str, password: str, database: str, admin_obj=None
) -> tuple[bool, bool, str, str | None]:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    db_url = save_db_url(host, port, user, password, database)

    ok, err = await test_connection(host, port, user, password, database)
    if not ok:
        return True, False, db_url, err

    os.environ["DATABASE_URL"] = db_url

    try:
        await _db.engine.dispose()
    except Exception:
        pass

    _rebuild_engine(db_url, admin_obj)
    await _db.create_all_tables(force=True)

    return True, True, db_url, None


def _rebuild_engine(db_url: str, admin_obj=None) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    new_engine = create_async_engine(db_url)
    _db.DATABASE_URL = db_url
    _db.engine = new_engine
    _db.async_session_maker = async_sessionmaker(
        new_engine, expire_on_commit=False, class_=AsyncSession
    )

    if admin_obj is not None:
        admin_obj.engine = new_engine
        for view in getattr(admin_obj, "_views", []):
            if hasattr(view, "engine"):
                view.engine = new_engine


async def recover_current_engine(admin_obj=None) -> bool:
    params = get_current_db_params()
    if not params:
        return False

    ok, _ = await test_connection(
        host=params["host"],
        port=int(params["port"]),
        user=params["user"],
        password=params["password"],
        database=params["database"],
    )
    if not ok:
        return False

    db_url = build_db_url(
        host=params["host"],
        port=int(params["port"]),
        user=params["user"],
        password=params["password"],
        database=params["database"],
    )

    os.environ["DATABASE_URL"] = db_url

    try:
        await _db.engine.dispose()
    except Exception:
        pass

    _rebuild_engine(db_url, admin_obj)

    try:
        await _db.create_all_tables(force=True)
    except Exception:
        pass

    return True
