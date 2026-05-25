import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

EXPORTS_DIR = BASE_DIR / "data" / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

USERS_JSON = "data/users.json"
APPS_JSON = "data/apps.json"
VERSIONS_JSON = "data/versions.json"
CATEGORIES_JSON = "data/categories.json"


def _read_env(key: str, default: str) -> str:
    val = os.getenv(key)
    if val:
        return val
    env_file = BASE_DIR.parent.parent / ".env"
    if env_file.is_file():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                if k.strip() == key:
                    return v.strip().strip("\"'")
    return default


MINIO_ENDPOINT = _read_env("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = _read_env("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = _read_env("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = _read_env("MINIO_BUCKET", "appstore")
MINIO_SECURE = _read_env("MINIO_SECURE", "false").lower() == "true"

UPLOAD_FOLDER_ICONS = "icons"
UPLOAD_FOLDER_SCREENSHOTS = "screenshots"
UPLOAD_FOLDER_APKS = "apks"
UPLOAD_FOLDER_AVATARS = "avatars"

SECRET_KEY = os.getenv("APPSTORE_SECRET_KEY", "torex-store-super-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

BASE_URL = os.getenv("APPSTORE_BASE_URL", "http://127.0.0.1:8001/appstore")

