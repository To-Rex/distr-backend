from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from apps.user.models import User, UserType, UserStatus
from apps.user.di import get_current_user_by_token
from apps.user.schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
)
from apps.activity.services.activity_service import ActivityService
from config.database import get_async_session
from config.security import get_password_hash

router = APIRouter(
    prefix="/user-manager",
    tags=["User Manager"],
)


def require_admin_or_manager(current_user: User) -> None:
    """Require ADMIN, MANAGER, SUPERADMIN, or CEO privileges."""
    allowed_roles = {
        UserType.ADMIN,
        UserType.MANAGER,
        UserType.SUPERADMIN,
        UserType.CEO,
    }
    if current_user.user_type not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin or Manager access required."
        )


@router.get("", response_model=List[UserResponse])
async def list_users(
    user_type: Optional[UserType] = Query(
        None, description="Filter by user type"),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    require_admin_or_manager(current_user)

    query = select(User).options(
        selectinload(User.manager),
        selectinload(User.company_rel),
        selectinload(User.branch_rel),
        selectinload(User.agents),
    )

    company_id = current_user.company_id
    manager_id = current_user.manager_id
    

    if user_type:
        query = query.where(User.user_type == user_type)
    if company_id:
        query = query.where(User.company_id == company_id)
    if manager_id:
        query = query.where(User.manager_id == manager_id)

    result = await session.execute(query)
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    # Users can view their own profile or admins/managers can view any
    if current_user.id != user_id:
        require_admin_or_manager(current_user)

    result = await session.execute(
        select(User)
        .options(
            selectinload(User.manager),
            selectinload(User.company_rel),
            selectinload(User.branch_rel),
            selectinload(User.agents),
        )
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/create", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    require_admin_or_manager(current_user)

    # Check if username or email already exists
    existing = await session.execute(
        select(User).where(
            (User.username == user_data.username) |
            (User.email == user_data.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists"
        )

    user_dict = user_data.model_dump(exclude_unset=True)
    user_dict["password"] = get_password_hash(user_dict["password"])

    new_user = User(**user_dict)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    result = await session.execute(
        select(User)
        .options(
            selectinload(User.manager),
            selectinload(User.company_rel),
            selectinload(User.branch_rel),
            selectinload(User.agents),
        )
        .where(User.id == new_user.id)
    )
    created_user = result.scalar_one_or_none()
    if created_user:
        ActivityService.log("user_created_by_admin", {
            "uz": f"Yangi foydalanuvchi qo'shildi {created_user.username}",
            "ru": f"Новый пользователь добавлен {created_user.username}",
            "en": f"New user added {created_user.username}",
        })
    return created_user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.id != user_id:
        require_admin_or_manager(current_user)

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password":
            setattr(user, field, get_password_hash(value))
        else:
            setattr(user, field, value)

    await session.commit()

    result = await session.execute(
        select(User)
        .options(
            selectinload(User.manager),
            selectinload(User.company_rel),
            selectinload(User.branch_rel),
            selectinload(User.agents),
        )
        .where(User.id == user_id)
    )
    updated_user = result.scalar_one_or_none()
    if updated_user:
        ActivityService.log("user_updated_by_admin", {
            "uz": f"Foydalanuvchi ma'lumotlari yangilandi {updated_user.username}",
            "ru": f"Данные пользователя обновлены {updated_user.username}",
            "en": f"User info updated {updated_user.username}",
        })
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    require_admin_or_manager(current_user)

    if current_user.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account through this endpoint"
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ActivityService.log("user_deleted_by_admin", {
        "uz": f"Foydalanuvchi o'chirildi {user.username}",
        "ru": f"Пользователь удален {user.username}",
        "en": f"User deleted {user.username}",
    })
    await session.execute(delete(User).where(User.id == user_id))
    await session.commit()

