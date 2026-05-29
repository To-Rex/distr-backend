from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.branch.models import Branch
from apps.branch.schemas import BranchCreate, BranchResponse, BranchUpdate
from apps.company.models import Company
from apps.user.di import get_current_user_by_token
from apps.user.models import User, UserType
from config.database import get_async_session

router = APIRouter(
    prefix="/branches",
    tags=["Branches"],
)


@router.post("/", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    branch_data: BranchCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type not in [UserType.SUPERADMIN, UserType.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if branch_data.company_id is not None:
        if not (0 <= branch_data.company_id <= 2147483647):
            raise HTTPException(status_code=400, detail="Invalid company_id")
        result = await session.execute(
            select(Company).where(Company.id == branch_data.company_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Company not found")

    new_branch = Branch(**branch_data.model_dump())
    session.add(new_branch)
    await session.commit()
    await session.refresh(new_branch)
    return new_branch


@router.get("/", response_model=list[BranchResponse])
async def list_branches(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
    skip: int = 0,
    limit: int = 100,
):
    result = await session.execute(select(Branch).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{branch_id}", response_model=BranchResponse)
async def get_branch(
    branch_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(Branch).where(Branch.id == branch_id))
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch


@router.put("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: int,
    branch_update: BranchUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type not in [UserType.SUPERADMIN, UserType.ADMIN]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = await session.execute(select(Branch).where(Branch.id == branch_id))
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    if branch_update.company_id is not None:
        if not (0 <= branch_update.company_id <= 2147483647):
            raise HTTPException(status_code=400, detail="Invalid company_id")
        company_result = await session.execute(
            select(Company).where(Company.id == branch_update.company_id)
        )
        if not company_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Company not found")

    update_data = branch_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(branch, field, value)

    await session.commit()
    await session.refresh(branch)
    return branch


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_branch(
    branch_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type != UserType.SUPERADMIN:
        raise HTTPException(
            status_code=403, detail="Only superadmin can delete branches"
        )

    result = await session.execute(select(Branch).where(Branch.id == branch_id))
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    await session.delete(branch)
    await session.commit()
