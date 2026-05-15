import uuid
from pathlib import Path
from typing import Optional

from apps.app_store.config import ICONS_DIR, SCREENSHOTS_DIR, APKS_DIR, AVATARS_DIR


class UploadService:
    @staticmethod
    def upload_icon(file_data: bytes, filename: str) -> dict:
        ext = Path(filename).suffix or ".png"
        unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
        file_path = ICONS_DIR / unique_name
        file_path.write_bytes(file_data)
        url = f"/appstore/uploads/icons/{unique_name}"
        return {"url": url}

    @staticmethod
    def upload_screenshot(file_data: bytes, filename: str) -> dict:
        ext = Path(filename).suffix or ".png"
        unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
        file_path = SCREENSHOTS_DIR / unique_name
        file_path.write_bytes(file_data)
        url = f"/appstore/uploads/screenshots/{unique_name}"
        return {"url": url}

    @staticmethod
    def upload_apk(file_data: bytes, filename: str) -> dict:
        ext = Path(filename).suffix or ".apk"
        unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
        file_path = APKS_DIR / unique_name
        file_path.write_bytes(file_data)
        file_size_mb = len(file_data) / (1024 * 1024)
        file_size_str = f"{file_size_mb:.1f} MB"
        return {
            "filePath": str(file_path),
            "fileSize": file_size_str,
            "versionName": "",
            "packageName": "",
            "minSdkVersion": "26",
        }

    @staticmethod
    def upload_avatar(file_data: bytes, filename: str) -> dict:
        ext = Path(filename).suffix or ".png"
        unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
        file_path = AVATARS_DIR / unique_name
        file_path.write_bytes(file_data)
        url = f"/appstore/uploads/avatars/{unique_name}"
        return {"url": url}

    @staticmethod
    def get_apk_file_path(file_url: str) -> Optional[str]:
        if file_url.startswith("uploads/apks/"):
            path = Path(file_url)
            return str(path) if path.exists() else None
        relative = (
            file_url.split("/uploads/apks/")[-1] if "/uploads/apks/" in file_url else ""
        )
        if not relative:
            return None
        path = APKS_DIR / relative
        return str(path) if path.exists() else None
