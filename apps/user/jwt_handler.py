from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from config.security import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_DAYS,
    REFRESH_TOKEN_EXPIRE_DAYS,
)


def _create_token(data: dict, token_type: str, expire_days: int) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=expire_days)
    to_encode.update({"exp": expire, "type": token_type})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(data: dict) -> str:
    return _create_token(data, "access", ACCESS_TOKEN_EXPIRE_DAYS)


def create_refresh_token(data: dict) -> str:
    return _create_token(data, "refresh", REFRESH_TOKEN_EXPIRE_DAYS)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_access_token(token: str) -> Optional[dict]:
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None


def verify_refresh_token(token: str) -> Optional[dict]:
    payload = decode_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None


def is_jwt_token(token: str) -> bool:
    return token.count(".") == 2 and len(token) > 50
