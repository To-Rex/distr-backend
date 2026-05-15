from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from apps.user.models import User, AccessToken
from config.database import get_async_session

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
        token: str,
        session: AsyncSession = Depends(get_async_session)
) -> User:
    # Use selectinload to eagerly fetch the manager relationship
    query = (
        select(AccessToken)
        .options(
            selectinload(AccessToken.user).selectinload(User.manager),
            selectinload(AccessToken.user).selectinload(User.company_rel)
        )
        .where(
            AccessToken.access_token == token,
            AccessToken.expires_in >= datetime.now(tz=None)
        )
    )
    result = await session.execute(query)
    access_token = result.scalar_one_or_none()

    if access_token is None:
        raise HTTPException(status_code=401)

    return access_token.user


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

# async def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     session: AsyncSession = Depends(get_async_session)
# ) -> User:

#     # 1. Search for the token and nested relationships
#     query = (
#         select(AccessToken)
#         .where(AccessToken.access_token == token)
#         # First, load the user connected to the token
#         .options(
#             selectinload(AccessToken.user)
#             # Then, load the company_rel connected to that user
#             .selectinload(User.company_rel)
#         )
#     )

#     result = await session.execute(query)
#     token_record = result.scalar_one_or_none()

#     # 2. Validation
#     if not token_record:
#         raise HTTPException(status_code=401, detail="Invalid token")

#     if token_record.expires_in < datetime.utcnow():
#         raise HTTPException(status_code=401, detail="Token expired")

#     # This user object now contains the company_rel data ready for Pydantic
#     return token_record.user
