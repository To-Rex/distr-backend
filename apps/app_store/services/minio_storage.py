from io import BytesIO
import json
from typing import Optional, Any
from pathlib import Path

from minio import Minio
from minio.error import S3Error

from apps.app_store.config import (
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET,
    MINIO_SECURE,
)

_client: Optional[Minio] = None


def _get_client() -> Minio:
    global _client
    if _client is None:
        client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE,
        )
        try:
            if not client.bucket_exists(MINIO_BUCKET):
                client.make_bucket(MINIO_BUCKET)
        except Exception as e:
            raise ConnectionError(
                f"MinIO ulanishda xato ({MINIO_ENDPOINT}): {e}"
            ) from e
        _client = client
    return _client


def upload_bytes(object_key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    client = _get_client()
    client.put_object(
        bucket_name=MINIO_BUCKET,
        object_name=object_key,
        data=BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return object_key


def delete_file(object_key: str) -> bool:
    client = _get_client()
    try:
        client.remove_object(MINIO_BUCKET, object_key)
        return True
    except S3Error:
        return False


def get_object(object_key: str) -> Optional[BytesIO]:
    client = _get_client()
    try:
        response = client.get_object(MINIO_BUCKET, object_key)
        data = BytesIO(response.read())
        response.close()
        response.release_conn()
        return data
    except S3Error:
        return None


def get_object_stat(object_key: str) -> Optional[dict]:
    client = _get_client()
    try:
        stat = client.stat_object(MINIO_BUCKET, object_key)
        return {
            "size": stat.size,
            "etag": stat.etag,
            "content_type": stat.content_type,
        }
    except S3Error:
        return None


def file_exists(object_key: str) -> bool:
    return get_object_stat(object_key) is not None


def delete_prefix(prefix: str) -> bool:
    client = _get_client()
    try:
        objects = client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=True)
        for obj in objects:
            client.remove_object(MINIO_BUCKET, obj.object_name)
        return True
    except S3Error:
        return False


def delete_all() -> bool:
    return delete_prefix("")


def list_keys(prefix: str) -> list[str]:
    client = _get_client()
    try:
        objects = client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=True)
        return [obj.object_name for obj in objects]
    except S3Error:
        return []


def download_to_dir(prefix: str, dest_dir: Path) -> int:
    client = _get_client()
    count = 0
    try:
        objects = client.list_objects(MINIO_BUCKET, prefix=prefix, recursive=True)
        for obj in objects:
            target_path = dest_dir / obj.object_name
            target_path.parent.mkdir(parents=True, exist_ok=True)
            response = client.get_object(MINIO_BUCKET, obj.object_name)
            target_path.write_bytes(response.read())
            response.close()
            response.release_conn()
            count += 1
    except S3Error:
        pass
    return count


def upload_dir(src_dir: Path, prefix: str) -> int:
    client = _get_client()
    count = 0
    for file_path in src_dir.rglob("*"):
        if not file_path.is_file():
            continue
        rel = str(file_path.relative_to(src_dir))
        object_key = f"{prefix}/{rel}" if prefix else rel
        content_type = _guess_content_type(object_key)
        client.fput_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_key,
            file_path=str(file_path),
            content_type=content_type,
        )
        count += 1
    return count


def get_json(object_key: str) -> list[dict[str, Any]]:
    data = get_object(object_key)
    if data is None:
        return []
    content = data.read()
    if not content:
        return []
    try:
        result = json.loads(content)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


def put_json(object_key: str, data: list[dict[str, Any]]) -> None:
    content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    upload_bytes(object_key, content, "application/json")


def _guess_content_type(object_key: str) -> str:
    ext = Path(object_key).suffix.lower()
    mapping = {
        ".apk": "application/vnd.android.package-archive",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".zip": "application/zip",
    }
    return mapping.get(ext, "application/octet-stream")
