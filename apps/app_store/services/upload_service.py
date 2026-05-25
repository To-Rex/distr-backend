import uuid
from pathlib import Path
from typing import Optional

from apps.app_store.config import (
    UPLOAD_FOLDER_ICONS,
    UPLOAD_FOLDER_SCREENSHOTS,
    UPLOAD_FOLDER_APKS,
    UPLOAD_FOLDER_AVATARS,
)
from apps.app_store.services.minio_storage import upload_bytes, file_exists


class UploadService:
    @staticmethod
    def upload_icon(file_data: bytes, filename: str) -> dict:
        ext = Path(filename).suffix or ".png"
        unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
        object_key = f"{UPLOAD_FOLDER_ICONS}/{unique_name}"
        upload_bytes(object_key, file_data, "image/png")
        url = f"/appstore/uploads/{object_key}"
        return {"url": url}

    @staticmethod
    def upload_screenshot(file_data: bytes, filename: str) -> dict:
        ext = Path(filename).suffix or ".png"
        unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
        object_key = f"{UPLOAD_FOLDER_SCREENSHOTS}/{unique_name}"
        upload_bytes(object_key, file_data, "image/png")
        url = f"/appstore/uploads/{object_key}"
        return {"url": url}

    @staticmethod
    def upload_apk(file_data: bytes, filename: str) -> dict:
        ext = Path(filename).suffix or ".apk"
        unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
        object_key = f"{UPLOAD_FOLDER_APKS}/{unique_name}"
        upload_bytes(object_key, file_data, "application/vnd.android.package-archive")
        file_size_mb = len(file_data) / (1024 * 1024)
        file_size_str = f"{file_size_mb:.1f} MB"
        return {
            "filePath": object_key,
            "fileSize": file_size_str,
            "versionName": "",
            "packageName": "",
            "minSdkVersion": "26",
        }

    @staticmethod
    def upload_avatar(file_data: bytes, filename: str) -> dict:
        ext = Path(filename).suffix or ".png"
        unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
        object_key = f"{UPLOAD_FOLDER_AVATARS}/{unique_name}"
        upload_bytes(object_key, file_data, "image/png")
        url = f"/appstore/uploads/{object_key}"
        return {"url": url}

    @staticmethod
    def get_apk_file_path(file_url: str) -> Optional[str]:
        if "/uploads/" in file_url:
            parts = file_url.split("/uploads/")
            if len(parts) > 1:
                key = parts[-1]
                return key if file_exists(key) else None
        return None

    @staticmethod
    def has_apk(file_path: str) -> bool:
        return bool(file_path and file_exists(file_path))
