from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.company.models import Company, SecurityKey
from apps.company.schemas import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    SecurityKeyCreate,
    SecurityKeyUpdate,
    SecurityKeyResponse,
)
from apps.user.models import User, UserType
from apps.user.di import get_current_user_by_token
from apps.activity.services.activity_service import ActivityService
from config.database import get_async_session

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


# --- Company CRUD ---

@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type not in [UserType.SUPERADMIN, UserType.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    result = await session.execute(select(Company).where(Company.name == company_data.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Company with this name already exists")
    
    new_company = Company(**company_data.model_dump())
    session.add(new_company)
    await session.commit()
    await session.refresh(new_company)
    ActivityService.log("company_created", {
        "uz": f"Yangi kompaniya ro'yxatdan o'tdi {new_company.name}",
        "ru": f"Новая компания зарегистрирована {new_company.name}",
        "en": f"New company registered {new_company.name}",
    })
    return new_company


@router.get("/", response_model=list[CompanyResponse])
async def list_companies(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
    skip: int = 0,
    limit: int = 100,
):
    result = await session.execute(select(Company).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    company_update: CompanyUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type not in [UserType.SUPERADMIN, UserType.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    result = await session.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    update_data = company_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    
    await session.commit()
    await session.refresh(company)
    ActivityService.log("company_updated", {
        "uz": f"Kompaniya ma'lumotlari yangilandi {company.name}",
        "ru": f"Данные компании обновлены {company.name}",
        "en": f"Company info updated {company.name}",
    })
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type != UserType.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only superadmin can delete companies")
    
    result = await session.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    ActivityService.log("company_deleted", {
        "uz": f"Kompaniya o'chirildi {company.name}",
        "ru": f"Компания удалена {company.name}",
        "en": f"Company deleted {company.name}",
    })
    await session.delete(company)
    await session.commit()


# --- SecurityKey CRUD ---

@router.post("/{company_id}/security-keys", response_model=SecurityKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_security_key(
    company_id: int,
    key_data: SecurityKeyCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type not in [UserType.SUPERADMIN, UserType.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if key_data.company_id != company_id:
        raise HTTPException(status_code=400, detail="Company ID mismatch")
    
    # Verify company exists
    company_result = await session.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check if key already exists
    existing_result = await session.execute(select(SecurityKey).where(SecurityKey.key == key_data.key))
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Security key already exists")
    
    new_key = SecurityKey(**key_data.model_dump())
    session.add(new_key)
    await session.commit()
    await session.refresh(new_key)
    return new_key


@router.get("/{company_id}/security-keys", response_model=list[SecurityKeyResponse])
async def list_security_keys(
    company_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(SecurityKey).where(SecurityKey.company_id == company_id))
    return result.scalars().all()


@router.get("/security-keys/{key_id}", response_model=SecurityKeyResponse)
async def get_security_key(
    key_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(SecurityKey).where(SecurityKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Security key not found")
    return key


@router.put("/security-keys/{key_id}", response_model=SecurityKeyResponse)
async def update_security_key(
    key_id: int,
    key_update: SecurityKeyUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type not in [UserType.SUPERADMIN, UserType.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    result = await session.execute(select(SecurityKey).where(SecurityKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Security key not found")
    
    update_data = key_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(key, field, value)
    
    await session.commit()
    await session.refresh(key)
    return key


@router.delete("/security-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_security_key(
    key_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type != UserType.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only superadmin can delete security keys")
    
    result = await session.execute(select(SecurityKey).where(SecurityKey.id == key_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Security key not found")
    
    await session.delete(key)
    await session.commit()
