from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from apps.app_store.utils.jwt_handler import verify_access_token
from apps.user.models import AccessToken
from config.database import async_session_maker

security = HTTPBearer()

ADMIN_USER_TYPES = {"SUPERADMIN", "ADMIN"}


async def _get_user_from_db_token(token_str: str) -> Optional[dict]:
    try:
        async with async_session_maker() as session:
            query = select(AccessToken).where(
                AccessToken.access_token == token_str,
                AccessToken.expires_in >= datetime.now(tz=None),
            )
            result = await session.execute(query)
            access_token = result.scalar_one_or_none()
            if not access_token:
                return None

            user = access_token.user
            role = "admin" if user.user_type.value in ADMIN_USER_TYPES else "publisher"

            return {
                "sub": str(user.id),
                "username": user.username,
                "role": role,
            }
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    payload = verify_access_token(credentials.credentials)
    if payload:
        return payload

    db_payload = await _get_user_from_db_token(credentials.credentials)
    if db_payload:
        return db_payload

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"success": False, "error": "Autentifikatsiya talab qilinadi"},
    )


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "error": "Faqat admin uchun"},
        )
    return current_user
