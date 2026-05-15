from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.device.models import Device
from apps.device.schemas import DeviceCreate, DeviceUpdate, DeviceResponse
from apps.user.models import User, UserType
from apps.user.di import get_current_user_by_token
from config.database import get_async_session

router = APIRouter(
    prefix="/devices",
    tags=["Devices"],
)


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type not in [UserType.SUPERADMIN, UserType.ADMIN, UserType.MANAGER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if device_uuid already exists
    result = await session.execute(select(Device).where(Device.device_uuid == device_data.device_uuid))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Device with this UUID already exists")
    
    # Validate user_id if provided
    if device_data.user_id:
        user_result = await session.execute(select(User).where(User.id == device_data.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
    new_device = Device(**device_data.model_dump())
    session.add(new_device)
    await session.commit()
    await session.refresh(new_device)
    return new_device


@router.get("/", response_model=list[DeviceResponse])
async def list_devices(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
    is_active: Optional[bool] = None,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
):
    query = select(Device)
    if is_active is not None:
        query = query.where(Device.is_active == is_active)
    if user_id is not None:
        query = query.where(Device.user_id == user_id)
    query = query.offset(skip).limit(limit).order_by(Device.created_at.desc())
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type not in [UserType.SUPERADMIN, UserType.ADMIN, UserType.MANAGER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    result = await session.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    update_data = device_update.model_dump(exclude_unset=True)
    
    # Validate user_id if being updated
    if "user_id" in update_data and update_data["user_id"] is not None:
        user_result = await session.execute(select(User).where(User.id == update_data["user_id"]))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
    for field, value in update_data.items():
        setattr(device, field, value)
    
    await session.commit()
    await session.refresh(device)
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type != UserType.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only superadmin can delete devices")
    
    result = await session.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    await session.delete(device)
    await session.commit()
