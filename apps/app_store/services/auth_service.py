from typing import Optional

import bcrypt

from apps.app_store.repositories.user_repository import UserRepository
from apps.app_store.utils.jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return _verify_password(plain_password, hashed_password)

    @staticmethod
    def hash_password(password: str) -> str:
        return _hash_password(password)

    @staticmethod
    def login(username: str, password: str) -> Optional[dict]:
        user = UserRepository.get_by_username(username)
        if not user:
            return None
        if not AuthService.verify_password(password, user["password"]):
            return None

        token_data = {
            "sub": user["id"],
            "username": user["username"],
            "role": user["role"],
        }
        token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "token": token,
            "refreshToken": refresh_token,
            "user": AuthService._user_response(user),
        }

    @staticmethod
    def refresh_token(refresh_token_str: str) -> Optional[dict]:
        payload = verify_refresh_token(refresh_token_str)
        if not payload:
            return None

        user = UserRepository.get_by_id(payload.get("sub"))
        if not user:
            return None

        token_data = {
            "sub": user["id"],
            "username": user["username"],
            "role": user["role"],
        }
        new_token = create_access_token(token_data)
        return {"token": new_token}

    @staticmethod
    def get_profile(user_id: str) -> Optional[dict]:
        user = UserRepository.get_by_id(user_id)
        if not user:
            return None
        return AuthService._user_response(user)

    @staticmethod
    def update_profile(
        user_id: str, display_name: Optional[str] = None, avatar: Optional[str] = None
    ) -> Optional[dict]:
        updates = {}
        if display_name is not None:
            updates["displayName"] = display_name
        if avatar is not None:
            updates["avatar"] = avatar
        if not updates:
            user = UserRepository.get_by_id(user_id)
            return AuthService._user_response(user) if user else None

        user = UserRepository.update(user_id, updates)
        return AuthService._user_response(user) if user else None

    @staticmethod
    def change_password(
        user_id: str, current_password: str, new_password: str
    ) -> tuple[bool, str]:
        user = UserRepository.get_by_id(user_id)
        if not user:
            return False, "Foydalanuvchi topilmadi"
        if not AuthService.verify_password(current_password, user["password"]):
            return False, "Joriy parol noto'g'ri"
        UserRepository.update(
            user_id, {"password": AuthService.hash_password(new_password)}
        )
        return True, "Parol muvaffaqiyatli o'zgartirildi"

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
