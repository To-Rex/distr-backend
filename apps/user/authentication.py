from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.user.models import User, AccessToken
from apps.user.jwt_handler import create_access_token as create_jwt_access, create_refresh_token
from config.security import verify_password, get_expiration_date


async def authenticate(username: str, password: str, fcm_token: str | None, session: AsyncSession) -> User | None:
    query = select(User).where(
        (User.username == username) | (User.email == username))
    result = await session.execute(query)
    user: User = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    if fcm_token is not None:
        user.fcm_token = fcm_token
        session.add(user)
        await session.commit()
    return user



async def create_access_token(user: User, session: AsyncSession) -> AccessToken | None:
    access_token = AccessToken(user=user)
    session.add(access_token)
    await session.commit()
    await session.refresh(access_token)
    return access_token


async def create_jwt_tokens(user: User) -> dict:
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "user_type": user.user_type.value,
    }
    jwt_access = create_jwt_access(token_data)
    refresh = create_refresh_token(token_data)

    return {
        "id": 0,
        "access_token": jwt_access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": get_expiration_date(),
        "user_id": user.id,
        "created_at": datetime.now(),
        "updated_at": None,
    }
