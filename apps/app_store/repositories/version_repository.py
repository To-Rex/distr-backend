from typing import Optional

from apps.app_store.config import VERSIONS_JSON
from apps.app_store.utils.minio_json_db import MinioJsonDB


class VersionRepository:
    @staticmethod
    def get_all() -> list[dict]:
        return MinioJsonDB.read(VERSIONS_JSON)

    @staticmethod
    def get_by_app(app_id: str) -> list[dict]:
        versions = MinioJsonDB.read(VERSIONS_JSON)
        return [v for v in versions if v["appId"] == app_id]

    @staticmethod
    def get_by_app_and_version(app_id: str, version: str) -> Optional[dict]:
        return MinioJsonDB.read_one(
            VERSIONS_JSON, lambda v: v["appId"] == app_id and v["version"] == version
        )

    @staticmethod
    def create(version: dict) -> dict:
        return MinioJsonDB.insert(VERSIONS_JSON, version)

    @staticmethod
    def update(app_id: str, version: str, updates: dict) -> Optional[dict]:
        return MinioJsonDB.update(
            VERSIONS_JSON,
            lambda v: v["appId"] == app_id and v["version"] == version,
            updates,
        )

    @staticmethod
    def delete(app_id: str, version: str) -> bool:
        return MinioJsonDB.delete(
            VERSIONS_JSON,
            lambda v: v["appId"] == app_id and v["version"] == version,
        )

    @staticmethod
    def delete_by_app(app_id: str) -> bool:
        versions = MinioJsonDB.read(VERSIONS_JSON)
        remaining = [v for v in versions if v["appId"] != app_id]
        MinioJsonDB.write(VERSIONS_JSON, remaining)
        return True

    @staticmethod
    def get_latest(app_id: str) -> Optional[dict]:
        versions = VersionRepository.get_by_app(app_id)
        latest = [v for v in versions if v.get("isLatest")]
        return latest[0] if latest else None

    @staticmethod
    def set_latest(app_id: str, version_str: str) -> None:
        versions = MinioJsonDB.read(VERSIONS_JSON)
        for v in versions:
            if v["appId"] == app_id:
                v["isLatest"] = v["version"] == version_str
        MinioJsonDB.write(VERSIONS_JSON, versions)

    @staticmethod
    def get_sorted(
        app_id: str, sort: str = "newest", page: int = 1, limit: int = 20
    ) -> tuple[list[dict], int]:
        versions = VersionRepository.get_by_app(app_id)
        reverse = sort == "newest"
        versions.sort(key=lambda v: v.get("releaseDate", ""), reverse=reverse)
        total = len(versions)
        start = (page - 1) * limit
        return versions[start : start + limit], total

    @staticmethod
    def increment_download(app_id: str, version: str) -> None:
        versions = MinioJsonDB.read(VERSIONS_JSON)
        for v in versions:
            if v["appId"] == app_id and v["version"] == version:
                v["downloadCount"] = v.get("downloadCount", 0) + 1
        MinioJsonDB.write(VERSIONS_JSON, versions)

    @staticmethod
    def total_download_count(app_id: str) -> int:
        versions = VersionRepository.get_by_app(app_id)
        return sum(v.get("downloadCount", 0) for v in versions)
