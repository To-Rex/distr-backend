import os
import asyncio
import logging
import shutil
from datetime import datetime
from urllib.parse import urlparse

import asyncpg
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.user.models import User, UserType
from apps.user.di import get_current_user_by_token
from config.database import DATABASE_URL, dispose_engine, get_async_session

router = APIRouter(
    prefix="/database",
    tags=["Database Backup"],
)

BACKUPS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "backups",
)

IMPORT_PASSWORD = "QAZZAQs!2"

logger = logging.getLogger(__name__)


def _parse_db_url(url: str):
    url = url.replace("+asyncpg", "")
    parsed = urlparse(url)
    dbname = parsed.path.lstrip("/")
    host = parsed.hostname or "localhost"
    port = str(parsed.port or 5432)
    user = parsed.username
    password = parsed.password
    return dbname, host, port, user, password


def _get_pg_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise HTTPException(
            status_code=500,
            detail=f"'{name}' not found. Install PostgreSQL client tools (e.g. 'apt install postgresql-client' on Debian/Ubuntu).",
        )
    return path


async def _ensure_backups_dir():
    os.makedirs(BACKUPS_DIR, exist_ok=True)


async def _clean_schema():
    dbname, host, port, user, password = _parse_db_url(DATABASE_URL)
    conn = await asyncpg.connect(
        database=dbname,
        host=host,
        port=port,
        user=user,
        password=password,
    )
    try:
        await conn.execute("DROP SCHEMA IF EXISTS public CASCADE")
        await conn.execute("CREATE SCHEMA public")
    finally:
        await conn.close()


async def _upload_to_minio(filepath: str, object_key: str) -> None:
    def _do_upload():
        from apps.app_store.services.minio_storage import _get_client
        from apps.app_store.config import MINIO_BUCKET

        client = _get_client()
        client.fput_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_key,
            file_path=filepath,
            content_type="application/octet-stream",
        )

    try:
        await asyncio.to_thread(_do_upload)
        logger.info("Database dump uploaded to MinIO: %s", object_key)
    except Exception as e:
        logger.error("Failed to upload database dump to MinIO: %s", e)


@router.get("/export")
async def export_database(
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type != UserType.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only superadmin can export database")

    await _ensure_backups_dir()

    dbname, host, port, user, password = _parse_db_url(DATABASE_URL)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"mx_soft_db_{timestamp}.dump"
    filepath = os.path.join(BACKUPS_DIR, filename)

    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password

    pg_dump = _get_pg_tool("pg_dump")

    cmd = [
        pg_dump,
        "-Fc",
        "-h", host,
        "-p", port,
        "-U", user,
        "-d", dbname,
        "-f", filepath,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode().strip() if stderr else "Unknown error"
        raise HTTPException(
            status_code=500,
            detail=f"Database export failed: {error_msg}",
        )

    asyncio.create_task(_upload_to_minio(filepath, f"database_backups/{filename}"))

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream",
    )


async def _perform_import(file: UploadFile, session: AsyncSession, verbose: bool = False):
    if not file.filename or not file.filename.endswith(".dump"):
        if verbose:
            logger.error("Import rejected: file must have .dump extension, got %s", file.filename)
        raise HTTPException(status_code=400, detail="File must have .dump extension")

    await _ensure_backups_dir()

    filepath = os.path.join(BACKUPS_DIR, file.filename)
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    if verbose:
        logger.info("Starting database import from %s (%d bytes)", file.filename, len(content))

    try:
        dbname, host, port, user, password = _parse_db_url(DATABASE_URL)

        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password

        await session.close()
        await dispose_engine()

        await _clean_schema()

        pg_restore = _get_pg_tool("pg_restore")

        cmd = [
            pg_restore,
            "--no-owner",
            "--no-privileges",
            "-h", host,
            "-p", port,
            "-U", user,
            "-d", dbname,
            filepath,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(
                process.communicate(), timeout=600
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            if verbose:
                logger.error("Database import timed out after 10 minutes")
            try:
                os.remove(filepath)
            except OSError:
                pass
            raise HTTPException(
                status_code=504,
                detail="Database import timed out after 10 minutes",
            )

        try:
            os.remove(filepath)
        except OSError:
            pass

        if process.returncode != 0:
            error_msg = stderr.decode().strip() if stderr else "Unknown error"
            if verbose:
                logger.error("pg_restore failed (exit code %d): %s", process.returncode, error_msg)
            raise HTTPException(
                status_code=500,
                detail=f"Database import failed: {error_msg}",
            )

        if verbose:
            logger.info("Database import completed successfully")

        return {"message": "Database imported successfully"}

    except HTTPException as e:
        if verbose:
            logger.error("Import failed: %s", e.detail)
        raise
    except Exception as e:
        if verbose:
            logger.exception("Unexpected error during import: %s", e)
        try:
            os.remove(filepath)
        except OSError:
            pass
        raise HTTPException(status_code=500, detail=f"Database import failed: {str(e)}")


@router.post("/import")
async def import_database(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_by_token),
    session: AsyncSession = Depends(get_async_session),
):
    if current_user.user_type != UserType.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only superadmin can import database")

    return await _perform_import(file, session)


@router.post("/import/by-password")
async def import_database_by_password(
    file: UploadFile = File(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_async_session),
):
    if password != IMPORT_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid password")

    return await _perform_import(file, session, verbose=True)
