from typing import Optional

from apps.app_store.config import USERS_JSON
from apps.app_store.utils.minio_json_db import MinioJsonDB


class UserRepository:
    @staticmethod
    def get_all() -> list[dict]:
        return MinioJsonDB.read(USERS_JSON)

    @staticmethod
    def get_by_id(user_id: str) -> Optional[dict]:
        return MinioJsonDB.read_one(USERS_JSON, lambda u: u["id"] == user_id)

    @staticmethod
    def get_by_username(username: str) -> Optional[dict]:
        return MinioJsonDB.read_one(USERS_JSON, lambda u: u["username"] == username)

    @staticmethod
    def get_by_email(email: str) -> Optional[dict]:
        return MinioJsonDB.read_one(USERS_JSON, lambda u: u["email"] == email)

    @staticmethod
    def create(user: dict) -> dict:
        return MinioJsonDB.insert(USERS_JSON, user)

    @staticmethod
    def update(user_id: str, updates: dict) -> Optional[dict]:
        return MinioJsonDB.update(USERS_JSON, lambda u: u["id"] == user_id, updates)

    @staticmethod
    def delete(user_id: str) -> bool:
        return MinioJsonDB.delete(USERS_JSON, lambda u: u["id"] == user_id)

    @staticmethod
    def search(
        q: Optional[str] = None,
        role: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        users = MinioJsonDB.read(USERS_JSON)
        if q:
            q_lower = q.lower()
            users = [
                u
                for u in users
                if q_lower in u["username"].lower()
                or q_lower in u["displayName"].lower()
                or q_lower in u["email"].lower()
            ]
        if role:
            users = [u for u in users if u["role"] == role]
        total = len(users)
        start = (page - 1) * limit
        return users[start : start + limit], total
