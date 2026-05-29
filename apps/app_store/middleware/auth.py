from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from apps.app_store.utils.jwt_handler import verify_access_token
from config.security import JWT_SECRET_KEY, JWT_ALGORITHM

security = HTTPBearer()

ADMIN_USER_TYPES = {"SUPERADMIN", "ADMIN"}


async def _get_user_from_main_api_jwt(token_str: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token_str, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        user_type = payload.get("user_type")
        if user_type not in ADMIN_USER_TYPES:
            return None
        return {
            "sub": payload.get("sub"),
            "username": payload.get("username"),
            "role": "admin",
        }
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    payload = verify_access_token(credentials.credentials)
    if payload:
        return payload

    main_api_payload = await _get_user_from_main_api_jwt(credentials.credentials)
    if main_api_payload:
        return main_api_payload

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
