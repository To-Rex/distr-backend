from typing import Optional

from apps.app_store.config import APPS_JSON
from apps.app_store.utils.minio_json_db import MinioJsonDB


class AppRepository:
    @staticmethod
    def get_all() -> list[dict]:
        return MinioJsonDB.read(APPS_JSON)

    @staticmethod
    def get_by_id(app_id: str) -> Optional[dict]:
        return MinioJsonDB.read_one(APPS_JSON, lambda a: a["id"] == app_id)

    @staticmethod
    def create(app: dict) -> dict:
        return MinioJsonDB.insert(APPS_JSON, app)

    @staticmethod
    def update(app_id: str, updates: dict) -> Optional[dict]:
        return MinioJsonDB.update(APPS_JSON, lambda a: a["id"] == app_id, updates)

    @staticmethod
    def delete(app_id: str) -> bool:
        return MinioJsonDB.delete(APPS_JSON, lambda a: a["id"] == app_id)

    @staticmethod
    def search(
        q: Optional[str] = None,
        category: Optional[str] = None,
        sort: str = "updated",
        published: Optional[bool] = None,
        page: int = 1,
        limit: int = 20,
        created_by: Optional[str] = None,
    ) -> tuple[list[dict], int]:
        apps = MinioJsonDB.read(APPS_JSON)

        if created_by:
            apps = [a for a in apps if a["createdBy"] == created_by]

        if published is not None:
            apps = [a for a in apps if a.get("published") == published]

        if q:
            q_lower = q.lower()
            apps = [
                a
                for a in apps
                if q_lower in a["name"].lower()
                or q_lower in a.get("shortDescription", "").lower()
                or q_lower in a.get("description", "").lower()
                or any(q_lower in tag.lower() for tag in a.get("tags", []))
            ]

        if category:
            apps = [a for a in apps if a.get("category") == category]

        sort_key = {
            "updated": lambda a: a.get("updatedAt", ""),
            "newest": lambda a: a.get("createdAt", ""),
            "downloads": lambda a: a.get("totalDownloads", 0),
            "name": lambda a: a.get("name", "").lower(),
        }.get(sort, lambda a: a.get("updatedAt", ""))

        reverse = sort != "name"
        apps.sort(key=sort_key, reverse=reverse)

        total = len(apps)
        start = (page - 1) * limit
        return apps[start : start + limit], total

    @staticmethod
    def get_featured(limit: int = 3) -> list[dict]:
        apps = MinioJsonDB.read(APPS_JSON)
        apps = [a for a in apps if a.get("published")]
        apps.sort(key=lambda a: a.get("totalDownloads", 0), reverse=True)
        return apps[:limit]

    @staticmethod
    def get_recently_updated(limit: int = 4) -> list[dict]:
        apps = MinioJsonDB.read(APPS_JSON)
        apps = [a for a in apps if a.get("published")]
        apps.sort(key=lambda a: a.get("updatedAt", ""), reverse=True)
        return apps[:limit]

    @staticmethod
    def get_newest(limit: int = 4) -> list[dict]:
        apps = MinioJsonDB.read(APPS_JSON)
        apps = [a for a in apps if a.get("published")]
        apps.sort(key=lambda a: a.get("createdAt", ""), reverse=True)
        return apps[:limit]

    @staticmethod
    def get_by_category() -> dict[str, int]:
        apps = MinioJsonDB.read(APPS_JSON)
        counts: dict[str, int] = {}
        for app in apps:
            cat = app.get("category", "")
            if cat:
                counts[cat] = counts.get(cat, 0) + 1
        return counts
