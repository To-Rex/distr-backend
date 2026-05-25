from typing import Optional

from apps.app_store.config import USERS_JSON
from apps.app_store.repositories.user_repository import UserRepository
from apps.app_store.repositories.app_repository import AppRepository
from apps.app_store.repositories.version_repository import VersionRepository
from apps.app_store.services.auth_service import AuthService


class UserService:
    @staticmethod
    def get_all(
        q: Optional[str] = None,
        role: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        users, total = UserRepository.search(q=q, role=role, page=page, limit=limit)
        result = [UserService._user_response(u) for u in users]
        return result, total

    @staticmethod
    def get_by_id(user_id: str) -> Optional[dict]:
        user = UserRepository.get_by_id(user_id)
        if not user:
            return None

        apps = AppRepository.get_all()
        user_apps = [a for a in apps if a.get("createdBy") == user_id]
        total_downloads = sum(a.get("totalDownloads", 0) for a in user_apps)

        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "displayName": user["displayName"],
            "avatar": user.get("avatar"),
            "createdAt": user["createdAt"],
            "appsCount": len(user_apps),
            "totalAppDownloads": total_downloads,
        }

    @staticmethod
    def create(
        username: str,
        email: str,
        password: str,
        display_name: str,
        role: str = "publisher",
    ) -> tuple[Optional[dict], Optional[str]]:
        existing_username = UserRepository.get_by_username(username)
        if existing_username:
            return None, "Bu username allaqachon mavjud"

        existing_email = UserRepository.get_by_email(email)
        if existing_email:
            return None, "Bu email allaqachon mavjud"

        from datetime import date

        today = date.today().isoformat()
        user_id = f"user-{int(date.today().strftime('%s'))}"

        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "password": AuthService.hash_password(password),
            "role": role,
            "displayName": display_name,
            "avatar": None,
            "createdAt": today,
        }
        UserRepository.create(user)
        return UserService._user_response(user), None

    @staticmethod
    def update(user_id: str, **kwargs) -> Optional[dict]:
        user = UserRepository.get_by_id(user_id)
        if not user:
            return None

        updates = {}
        if "displayName" in kwargs and kwargs["displayName"] is not None:
            updates["displayName"] = kwargs["displayName"]
        if "email" in kwargs and kwargs["email"] is not None:
            updates["email"] = kwargs["email"]
        if "role" in kwargs and kwargs["role"] is not None:
            updates["role"] = kwargs["role"]
        if "password" in kwargs and kwargs["password"] is not None:
            updates["password"] = AuthService.hash_password(kwargs["password"])

        if updates:
            UserRepository.update(user_id, updates)

        updated = UserRepository.get_by_id(user_id)
        return UserService._user_response(updated) if updated else None

    @staticmethod
    def delete(user_id: str) -> bool:
        return UserRepository.delete(user_id)

    @staticmethod
    def _user_response(user: dict) -> dict:
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "displayName": user["displayName"],
            "avatar": user.get("avatar"),
            "createdAt": user["createdAt"],
        }
