from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.user.models import User, AccessToken
from config.security import verify_password


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


async def authenticate_without_fcm_token(username: str, password: str, session: AsyncSession) -> User | None:
    query = select(User).where(
        (User.username == username) | (User.email == username))
    result = await session.execute(query)
    user: User = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


async def create_access_token(user: User, session: AsyncSession, ) -> AccessToken | None:
    access_token = AccessToken(user=user)
    session.add(access_token)
    await session.commit()
    await session.refresh(access_token)
    return access_token
