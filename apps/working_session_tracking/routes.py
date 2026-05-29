from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, defaultload, selectinload

from apps.working_session_tracking.models import WorkingSession
from apps.working_session_tracking.schemas import (
    WorkingSessionCreate,
    WorkingSessionResponse,
    WorkerSessionResponse,
)
from apps.user.models import User
from apps.user.di import get_current_user_by_token
from apps.user.schemas import UserResponse
from config.database import get_async_session

router = APIRouter(
    prefix="/working-sessions",
    tags=["Working Sessions"],
)


@router.post("/create", response_model=WorkingSessionResponse, status_code=201)
async def create_working_session(
    session_data: WorkingSessionCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_session = WorkingSession(
        session=session_data.session,
        device_name=session_data.device_name,
        user_id=current_user.id,
        app=session_data.app,
        is_testing=session_data.is_testing,
    )
    session.add(new_session)
    await session.commit()
    await session.refresh(new_session)
    return new_session


@router.get("", response_model=list[WorkerSessionResponse])
async def list_working_sessions(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    earliest_subq = (
        select(
            WorkingSession.user_id,
            func.min(WorkingSession.session).label("min_session"),
        )
        #.where(func.date(WorkingSession.session) == date.today())
        .where(func.date(WorkingSession.session) == (date.today() - timedelta(days=1)))
        .group_by(WorkingSession.user_id)
        .subquery()
    )

    result = await session.execute(
        select(WorkingSession)
        .options(
            joinedload(WorkingSession.user_rel),
            defaultload(WorkingSession.user_rel).selectinload(User.company_rel),
            defaultload(WorkingSession.user_rel).selectinload(User.manager),
        )
        .join(
            earliest_subq,
            (WorkingSession.user_id == earliest_subq.c.user_id)
            & (WorkingSession.session == earliest_subq.c.min_session),
        )
    )
    return [
        WorkerSessionResponse(
            user=UserResponse.model_validate(ws.user_rel),
            session=WorkingSessionResponse.model_validate(ws),
        )
        for ws in result.scalars().all()
    ]


@router.get("/{session_id}", response_model=WorkingSessionResponse)
async def get_working_session(
    session_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(
        select(WorkingSession).where(WorkingSession.id == session_id)
    )
    working_session = result.scalar_one_or_none()
    if not working_session:
        raise HTTPException(
            status_code=404, detail="Working session not found")
    return working_session


@router.get("/user/{user_id}", response_model=list[WorkingSessionResponse])
async def get_user_working_sessions(
    user_id: int,
    app: str | None = None,
    is_testing: bool | None = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    query = select(WorkingSession).where(WorkingSession.user_id == user_id)
    if app is not None and app != "mx-manager":
        query = query.where(WorkingSession.app == app)

    if is_testing is not None:
        query = query.where(WorkingSession.is_testing == is_testing)
    query = query.order_by(WorkingSession.session.desc())

    result = await session.execute(query)
    return result.scalars().all()


@router.delete("/{session_id}", status_code=204)
async def delete_working_session(
    session_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(
        select(WorkingSession).where(WorkingSession.id == session_id)
    )
    working_session = result.scalar_one_or_none()
    if not working_session:
        raise HTTPException(
            status_code=404, detail="Working session not found")

    await session.delete(working_session)
    await session.commit()
