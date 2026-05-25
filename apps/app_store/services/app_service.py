import uuid
from datetime import date
from typing import Optional

from slugify import slugify

from apps.app_store.config import BASE_URL
from apps.app_store.repositories.app_repository import AppRepository
from apps.app_store.repositories.user_repository import UserRepository
from apps.app_store.repositories.version_repository import VersionRepository
from apps.app_store.services.minio_storage import delete_file, file_exists


class AppService:
    @staticmethod
    def get_public_list(
        q: Optional[str] = None,
        category: Optional[str] = None,
        sort: str = "updated",
        page: int = 1,
        limit: int = 20,
        published: Optional[bool] = True,
    ) -> tuple[list[dict], int]:
        apps, total = AppRepository.search(
            q=q,
            category=category,
            sort=sort,
            published=published,
            page=page,
            limit=limit,
        )
        result = []
        for app in apps:
            item = AppService._public_summary(app)
            result.append(item)
        return result, total

    @staticmethod
    def get_by_id(app_id: str) -> Optional[dict]:
        app = AppRepository.get_by_id(app_id)
        if not app:
            return None
        return AppService._full_detail(app)

    @staticmethod
    def get_featured(limit: int = 3) -> list[dict]:
        apps = AppRepository.get_featured(limit)
        return [AppService._public_summary(a) for a in apps]

    @staticmethod
    def get_recently_updated(limit: int = 4) -> list[dict]:
        apps = AppRepository.get_recently_updated(limit)
        return [AppService._public_summary(a) for a in apps]

    @staticmethod
    def get_newest(limit: int = 4) -> list[dict]:
        apps = AppRepository.get_newest(limit)
        return [AppService._public_summary(a) for a in apps]

    @staticmethod
    def get_search_suggestions(q: str, limit: int = 5) -> list[dict]:
        apps = AppRepository.search(q=q, published=True, limit=limit, page=1)[0]
        result = []
        for app in apps:
            latest = VersionRepository.get_latest(app["id"])
            result.append(
                {
                    "id": app["id"],
                    "name": app["name"],
                    "icon": app.get("icon", ""),
                    "category": app.get("category", ""),
                    "latestVersion": latest["version"] if latest else "",
                }
            )
        return result

    @staticmethod
    def get_screenshots(app_id: str) -> Optional[dict]:
        app = AppRepository.get_by_id(app_id)
        if not app:
            return None
        screenshots = app.get("screenshots", [])
        result = []
        for idx, url in enumerate(screenshots):
            result.append({"id": idx + 1, "url": url, "order": idx + 1})
        return {"appId": app_id, "appName": app["name"], "screenshots": result}

    @staticmethod
    def create_app(
        user_id: str,
        name: str,
        developer: str,
        short_description: str,
        category: str,
        description: str = "",
        tags_str: str = "",
        icon: Optional[str] = None,
        published: bool = False,
    ) -> dict:
        today = date.today().isoformat()
        slug = slugify(name)
        app_id = f"{slug}-{int(date.today().strftime('%s'))}" if len(slug) < 2 else slug

        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

        app = {
            "id": app_id,
            "name": name,
            "icon": icon or "",
            "developer": developer,
            "shortDescription": short_description,
            "description": description,
            "category": category,
            "tags": tags,
            "screenshots": [],
            "totalDownloads": 0,
            "published": published,
            "createdBy": user_id,
            "updatedAt": today,
            "createdAt": today,
        }
        AppRepository.create(app)
        return app

    @staticmethod
    def update_app(app_id: str, **kwargs) -> Optional[dict]:
        app = AppRepository.get_by_id(app_id)
        if not app:
            return None

        updates = {}
        for key, value in kwargs.items():
            if value is not None:
                updates[key] = value

        if updates:
            from datetime import date as d

            updates["updatedAt"] = d.today().isoformat()
            AppRepository.update(app_id, updates)

        return AppRepository.get_by_id(app_id)

    @staticmethod
    def _delete_file_by_url(url: str):
        if not url:
            return
        if "/uploads/" in url:
            object_key = url.split("/uploads/")[-1]
            delete_file(object_key)

    @staticmethod
    def delete_app(app_id: str) -> bool:
        app = AppRepository.get_by_id(app_id)
        if not app:
            return False

        AppService._delete_file_by_url(app.get("icon", ""))

        for url in app.get("screenshots", []):
            AppService._delete_file_by_url(url)

        versions = VersionRepository.get_by_app(app_id)
        for v in versions:
            file_path = v.get("filePath")
            if file_path:
                delete_file(file_path)

        VersionRepository.delete_by_app(app_id)
        return AppRepository.delete(app_id)

    @staticmethod
    def toggle_publish(app_id: str) -> Optional[dict]:
        app = AppRepository.get_by_id(app_id)
        if not app:
            return None
        new_state = not app.get("published", False)
        AppRepository.update(app_id, {"published": new_state})
        return {"id": app_id, "published": new_state}

    @staticmethod
    def get_admin_list(
        user_id: str,
        user_role: str,
        page: int = 1,
        limit: int = 20,
        published: Optional[bool] = None,
    ) -> tuple[list[dict], int]:
        created_by = None if user_role == "admin" else user_id
        apps, total = AppRepository.search(
            published=published, page=page, limit=limit, created_by=created_by
        )
        result = []
        for app in apps:
            item = AppService._admin_detail(app)
            result.append(item)
        return result, total

    @staticmethod
    def get_admin_by_id(app_id: str) -> Optional[dict]:
        app = AppRepository.get_by_id(app_id)
        if not app:
            return None
        return AppService._admin_detail(app)

    @staticmethod
    def _has_apk(app_id: str) -> bool:
        latest = VersionRepository.get_latest(app_id)
        if not latest:
            return False
        file_path = latest.get("filePath", "")
        return bool(file_path and file_exists(file_path))

    @staticmethod
    def _public_summary(app: dict) -> dict:
        latest = VersionRepository.get_latest(app["id"])
        return {
            "id": app["id"],
            "name": app["name"],
            "icon": app.get("icon", ""),
            "developer": app.get("developer", ""),
            "shortDescription": app.get("shortDescription", ""),
            "category": app.get("category", ""),
            "tags": app.get("tags", []),
            "totalDownloads": app.get("totalDownloads", 0),
            "latestVersion": latest["version"] if latest else "",
            "hasApk": AppService._has_apk(app["id"]),
            "updatedAt": app.get("updatedAt", ""),
            "createdAt": app.get("createdAt", ""),
            "published": app.get("published", False),
        }

    @staticmethod
    def _full_detail(app: dict) -> dict:
        versions = VersionRepository.get_by_app(app["id"])
        version_list = [AppService._version_response(v) for v in versions]
        has_apk = any(
            v.get("filePath") and file_exists(v["filePath"]) for v in versions
        )
        return {
            "id": app["id"],
            "name": app["name"],
            "icon": app.get("icon", ""),
            "developer": app.get("developer", ""),
            "shortDescription": app.get("shortDescription", ""),
            "description": app.get("description", ""),
            "category": app.get("category", ""),
            "tags": app.get("tags", []),
            "screenshots": app.get("screenshots", []),
            "versions": version_list,
            "hasApk": has_apk,
            "totalDownloads": app.get("totalDownloads", 0),
            "updatedAt": app.get("updatedAt", ""),
            "createdAt": app.get("createdAt", ""),
            "published": app.get("published", False),
            "createdBy": app.get("createdBy", ""),
        }

    @staticmethod
    def _admin_detail(app: dict) -> dict:
        versions = VersionRepository.get_by_app(app["id"])
        version_list = [AppService._version_response(v) for v in versions]
        creator = UserRepository.get_by_id(app.get("createdBy", ""))
        has_apk = any(
            v.get("filePath") and file_exists(v["filePath"]) for v in versions
        )
        return {
            "id": app["id"],
            "name": app["name"],
            "icon": app.get("icon", ""),
            "developer": app.get("developer", ""),
            "shortDescription": app.get("shortDescription", ""),
            "description": app.get("description", ""),
            "category": app.get("category", ""),
            "tags": app.get("tags", []),
            "screenshots": app.get("screenshots", []),
            "versions": version_list,
            "hasApk": has_apk,
            "totalDownloads": app.get("totalDownloads", 0),
            "published": app.get("published", False),
            "createdBy": app.get("createdBy", ""),
            "creatorName": creator["displayName"] if creator else "",
            "updatedAt": app.get("updatedAt", ""),
            "createdAt": app.get("createdAt", ""),
        }

    @staticmethod
    def _version_response(v: dict) -> dict:
        file_path = v.get("filePath", "")
        return {
            "version": v["version"],
            "releaseDate": v.get("releaseDate", ""),
            "fileSize": v.get("fileSize", ""),
            "minAndroid": v.get("minAndroid", "8.0"),
            "changelog": v.get("changelog", ""),
            "downloadUrl": f"{BASE_URL}/apps/{v['appId']}/versions/{v['version']}/download",
            "downloadCount": v.get("downloadCount", 0),
            "isLatest": v.get("isLatest", False),
            "hasApk": bool(file_path and file_exists(file_path)),
        }
