from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from apps.alembic_version.models import AlembicVersion
from apps.alembic_version.schemas import AlembicVersionCreate, AlembicVersionResponse
from apps.user.di import get_current_user_by_token
from apps.user.models import User, UserType
from config.database import get_async_session

router = APIRouter(
    prefix="/admin/alembic-version",
    tags=["Admin - Alembic Version"],
)


@router.get(
    "/list",
    response_model=list[AlembicVersionResponse],
    summary="Alembic migration versiyalari ro'yxati",
    description="Bazadagi barcha alembic migration versiyalarini qaytaradi. Faqat SUPERADMIN uchun.",
)
async def list_alembic_versions(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type != UserType.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can access alembic version info",
        )

    result = await session.execute(select(AlembicVersion))
    return result.scalars().all()


@router.post(
    "/create",
    response_model=AlembicVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yangi alembic migration versiyasi yaratish",
    description="Yangi alembic migration versiyasini bazaga qo'shadi. Faqat SUPERADMIN uchun.",
)
async def create_alembic_version(
    data: AlembicVersionCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type != UserType.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can create alembic versions",
        )

    existing = await session.execute(
        select(AlembicVersion).where(AlembicVersion.version_num == data.version_num)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This version_num already exists",
        )

    new_version = AlembicVersion(version_num=data.version_num)
    session.add(new_version)
    await session.commit()
    await session.refresh(new_version)
    return new_version


@router.delete(
    "/{version_num}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Alembic migration versiyasini o'chirish",
    description="Berilgan version_num bo'yicha alembic versiyasini o'chiradi. Faqat SUPERADMIN uchun.",
)
async def delete_alembic_version(
    version_num: str,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type != UserType.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can delete alembic versions",
        )

    result = await session.execute(
        select(AlembicVersion).where(AlembicVersion.version_num == version_num)
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alembic version not found",
        )

    await session.delete(version)
    await session.commit()
