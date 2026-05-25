from datetime import date
from typing import Optional

from apps.app_store.config import BASE_URL
from apps.app_store.repositories.app_repository import AppRepository
from apps.app_store.repositories.version_repository import VersionRepository
from apps.app_store.services.minio_storage import delete_file


class VersionService:
    @staticmethod
    def get_versions(
        app_id: str, sort: str = "newest", page: int = 1, limit: int = 20
    ) -> Optional[tuple[list[dict], int]]:
        app = AppRepository.get_by_id(app_id)
        if not app:
            return None

        versions, total = VersionRepository.get_sorted(
            app_id, sort=sort, page=page, limit=limit
        )
        result = [VersionService._version_response(v) for v in versions]
        return result, total

    @staticmethod
    def get_single_version(app_id: str, version: str) -> Optional[dict]:
        v = VersionRepository.get_by_app_and_version(app_id, version)
        if not v:
            return None

        app = AppRepository.get_by_id(app_id)
        latest = VersionRepository.get_latest(app_id)

        return {
            "appId": app_id,
            "appName": app["name"] if app else "",
            "appIcon": app.get("icon", "") if app else "",
            "version": v["version"],
            "releaseDate": v.get("releaseDate", ""),
            "fileSize": v.get("fileSize", ""),
            "minAndroid": v.get("minAndroid", "8.0"),
            "changelog": v.get("changelog", ""),
            "downloadUrl": f"{BASE_URL}/apps/{app_id}/versions/{v['version']}/download",
            "downloadCount": v.get("downloadCount", 0),
            "isLatest": v.get("isLatest", False),
            "isNewerAvailable": latest["version"] != v["version"] if latest else False,
            "latestVersion": latest["version"] if latest else v["version"],
        }

    @staticmethod
    def download_version(app_id: str, version: str) -> Optional[dict]:
        v = VersionRepository.get_by_app_and_version(app_id, version)
        if not v:
            return None

        VersionRepository.increment_download(app_id, version)
        total = VersionRepository.total_download_count(app_id)
        AppRepository.update(app_id, {"totalDownloads": total})

        return v

    @staticmethod
    def create_version(
        app_id: str,
        version: str,
        file_size: str,
        min_android: str = "8.0",
        changelog: str = "",
        file_path: str = "",
    ) -> Optional[dict]:
        app = AppRepository.get_by_id(app_id)
        if not app:
            return None

        existing = VersionRepository.get_by_app_and_version(app_id, version)
        if existing:
            return None

        today = date.today().isoformat()

        VersionRepository.set_latest(app_id, version)

        version_data = {
            "appId": app_id,
            "version": version,
            "releaseDate": today,
            "fileSize": file_size,
            "minAndroid": min_android,
            "changelog": changelog,
            "filePath": file_path,
            "downloadCount": 0,
            "isLatest": True,
        }
        VersionRepository.create(version_data)
        AppRepository.update(app_id, {"updatedAt": today})

        return {
            "version": version,
            "releaseDate": today,
            "fileSize": file_size,
            "minAndroid": min_android,
            "changelog": changelog,
            "downloadUrl": f"{BASE_URL}/apps/{app_id}/versions/{version}/download",
            "downloadCount": 0,
            "isLatest": True,
        }

    @staticmethod
    def update_version(
        app_id: str,
        version: str,
        changelog: Optional[str] = None,
        min_android: Optional[str] = None,
        file_size: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> Optional[dict]:
        v = VersionRepository.get_by_app_and_version(app_id, version)
        if not v:
            return None

        updates = {}
        if changelog is not None:
            updates["changelog"] = changelog
        if min_android is not None:
            updates["minAndroid"] = min_android
        if file_size is not None:
            updates["fileSize"] = file_size
        if file_path is not None:
            updates["filePath"] = file_path

        if updates:
            VersionRepository.update(app_id, version, updates)

        updated = VersionRepository.get_by_app_and_version(app_id, version)
        return {
            "version": updated["version"],
            "releaseDate": updated.get("releaseDate", ""),
            "fileSize": updated.get("fileSize", ""),
            "minAndroid": updated.get("minAndroid", "8.0"),
            "changelog": updated.get("changelog", ""),
            "downloadUrl": f"{BASE_URL}/apps/{app_id}/versions/{updated['version']}/download",
            "downloadCount": updated.get("downloadCount", 0),
            "isLatest": updated.get("isLatest", False),
        }

    @staticmethod
    def delete_version(app_id: str, version: str) -> bool:
        v = VersionRepository.get_by_app_and_version(app_id, version)
        if not v:
            return False

        file_path = v.get("filePath")
        if file_path:
            delete_file(file_path)

        deleted = VersionRepository.delete(app_id, version)
        if deleted:
            remaining = VersionRepository.get_by_app(app_id)
            if remaining:
                from apps.app_store.repositories.version_repository import VersionRepository as VR

                latest = max(remaining, key=lambda v: v.get("releaseDate", ""))
                VR.set_latest(app_id, latest["version"])
        return deleted

    @staticmethod
    def _version_response(v: dict) -> dict:
        return {
            "version": v["version"],
            "releaseDate": v.get("releaseDate", ""),
            "fileSize": v.get("fileSize", ""),
            "minAndroid": v.get("minAndroid", "8.0"),
            "changelog": v.get("changelog", ""),
            "downloadUrl": f"{BASE_URL}/apps/{v['appId']}/versions/{v['version']}/download",
            "downloadCount": v.get("downloadCount", 0),
            "isLatest": v.get("isLatest", False),
        }
