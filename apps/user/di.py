from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from apps.user.models import User, AccessToken
from apps.user.jwt_handler import verify_access_token, is_jwt_token
from config.database import get_async_session

bearer_scheme = HTTPBearer(auto_error=False)


async def _resolve_user_by_id(user_id: int, session: AsyncSession) -> User | None:
    query = (
        select(User)
        .options(
            selectinload(User.manager),
            selectinload(User.company_rel),
            selectinload(User.branch_rel),
        )
        .where(User.id == user_id)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def _resolve_user_by_legacy_token(token: str, session: AsyncSession) -> User | None:
    query = (
        select(AccessToken)
        .options(
            selectinload(AccessToken.user).selectinload(User.manager),
            selectinload(AccessToken.user).selectinload(User.company_rel),
            selectinload(AccessToken.user).selectinload(User.branch_rel),
        )
        .where(
            AccessToken.access_token == token,
            AccessToken.expires_in >= datetime.now(tz=None)
        )
    )
    result = await session.execute(query)
    access_token = result.scalar_one_or_none()
    if access_token is None:
        return None
    return access_token.user


async def get_current_user(
        token: str,
        session: AsyncSession = Depends(get_async_session)
) -> User:
    if is_jwt_token(token):
        payload = verify_access_token(token)
        if payload is not None:
            user = await _resolve_user_by_id(int(payload["sub"]), session)
            if user is not None:
                return user
        raise HTTPException(status_code=401)

    user = await _resolve_user_by_legacy_token(token, session)
    if user is None:
        raise HTTPException(status_code=401)
    return user


async def get_current_user_by_token(
        bearer_credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
        request: Request,
        session: Annotated[AsyncSession, Depends(get_async_session)]
):
    token = bearer_credentials.credentials if bearer_credentials else None
    if not token:
        token = request.headers.get("X-API-KEY")
    user = await get_current_user(token, session)
    return user
