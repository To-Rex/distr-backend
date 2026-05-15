from datetime import datetime
from sqlalchemy.orm import contains_eager
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from firebase_admin import messaging
from apps.notification.models import Notification, NotificationUserStatus
from apps.notification.schemas import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
    NotificationUserStatusResponse,
    UnreadCountResponse,
)
from apps.user.models import User
from apps.user.di import get_current_user_by_token
from apps.company.models import Company, SecurityKey
from config.database import get_async_session

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)

# --- CREATE & LIST ---


@router.post("/create", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_data: NotificationCreate,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        # 1. Validate Security Key
        if notification_data.security_key:
            res = await session.execute(select(SecurityKey).where(SecurityKey.key == notification_data.security_key))
            security_key_obj = res.scalar_one_or_none()
            if not security_key_obj:
                raise HTTPException(
                    status_code=400, detail="Invalid security key")

            if notification_data.company_id and security_key_obj.company_id != notification_data.company_id:
                raise HTTPException(
                    status_code=400, detail="Security key mismatch for company")

        # 2. Validate Company
        if notification_data.company_id:
            res = await session.execute(select(Company).where(Company.id == notification_data.company_id))
            if not res.scalar_one_or_none():
                raise HTTPException(
                    status_code=404, detail="Company not found")

        new_notification = Notification(
            **notification_data.model_dump(exclude={'security_key'}))
        session.add(new_notification)
        await session.commit()
        await session.refresh(new_notification)

        query = select(User).where(
            User.company_id == notification_data.company_id,
            User.user_1c_id == notification_data.user_1c_id
        )
        result = await session.execute(query)
        target_user = result.scalar_one_or_none()

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=new_notification.title,
                    body=new_notification.message
                ),
                token=target_user.fcm_token
            )
            response = messaging.send(message)
            print(f"Successfully sent message: {response}")
        except Exception as fcm_error:
            print(f"FCM Failed: {fcm_error}")
            # We don't necessarily want to crash the whole request
            # if the DB part succeeded but only the push failed.

        return new_notification
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Database error: {str(e)}")


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    company_id: Optional[int] = None,
    user_1c_id: Optional[int] = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):

    query = (
        select(Notification)
        .outerjoin(
            NotificationUserStatus,
            and_(
                NotificationUserStatus.notification_id == Notification.id,
                NotificationUserStatus.user_id == current_user.id
            )
        )
    )

    if company_id is not None:
        query = query.where(Notification.company_id == company_id)
    if user_1c_id is not None:
        query = query.where(Notification.user_1c_id == user_1c_id)

    # Use contains_eager to tell SQLAlchemy the join already loaded the relationship
    query = query.options(contains_eager(Notification.user_statuses))

    result = await session.execute(query.order_by(Notification.created_at.desc()))
    notifications = result.scalars().unique().all()

    for n in notifications:
        # Pydantic expects 'status', but SQLAlchemy loaded 'user_statuses'
        n.status = n.user_statuses[0] if n.user_statuses else None

    return notifications


# --- SINGLE RESOURCE OPERATIONS ---


@router.get("/user", response_model=List[NotificationResponse])
async def get_user_notifications(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    query = (
        select(Notification)
        .outerjoin(
            NotificationUserStatus,
            and_(
                NotificationUserStatus.notification_id == Notification.id,
                NotificationUserStatus.user_id == current_user.id
            )
        )
    )

    query = query.where(Notification.user_1c_id == current_user.user_1c_id)

    query = query.options(contains_eager(Notification.user_statuses))

    result = await session.execute(query.order_by(Notification.created_at.desc()))
    notifications = result.scalars().unique().all()

    for n in notifications:
        # Pydantic expects 'status', but SQLAlchemy loaded 'user_statuses'
        n.status = n.user_statuses[0] if n.user_statuses else None

    return notifications


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    await session.delete(notification)
    await session.commit()

# --- TARGETED LISTS ---


@router.get("/company/{company_id}", response_model=List[NotificationResponse])
async def get_company_notifications(
    company_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    query = select(Notification).where(Notification.company_id ==
                                       company_id).order_by(Notification.created_at.desc())
    result = await session.execute(query)
    return result.scalars().all()

# --- READ / UNREAD STATUS ---


@router.post("/{notification_id}/read", response_model=NotificationUserStatusResponse)
async def mark_notification_as_read(
    notification_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(
        select(NotificationUserStatus).where(
            NotificationUserStatus.notification_id == notification_id,
            NotificationUserStatus.user_id == current_user.id
        )
    )
    status_record = result.scalar_one_or_none()

    if status_record:
        status_record.is_read = True
        status_record.read_at = datetime.now()
    else:
        status_record = NotificationUserStatus(
            notification_id=notification_id,
            user_id=current_user.id,
            is_read=True,
            read_at=datetime.now()
        )
        session.add(status_record)

    await session.commit()
    await session.refresh(status_record)
    return status_record


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    # Optimized query: Find all relevant notifications that DON'T have a 'read' status record for this user
    # Or have a status record where is_read is False
    stmt = select(Notification.id).where(
        or_(
            Notification.user_1c_id == current_user.user_1c_id,
            Notification.company_id == current_user.company_id
        )
    )
    res = await session.execute(stmt)
    relevant_ids = [row[0] for row in res.fetchall()]

    if not relevant_ids:
        return UnreadCountResponse(unread_count=0)

    read_stmt = select(NotificationUserStatus.notification_id).where(
        NotificationUserStatus.notification_id.in_(relevant_ids),
        NotificationUserStatus.user_id == current_user.id,
        NotificationUserStatus.is_read == True
    )
    read_res = await session.execute(read_stmt)
    read_ids = {row[0] for row in read_res.fetchall()}

    return UnreadCountResponse(unread_count=len(set(relevant_ids) - read_ids))


@router.post("/read-multiple", status_code=200)
async def mark_multiple_as_read(
    notification_ids: List[int],
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if not notification_ids:
        return {"message": "No IDs provided"}

    now = datetime.now()
    for nid in notification_ids:
        # Upsert logic
        stmt = select(NotificationUserStatus).where(
            NotificationUserStatus.notification_id == nid,
            NotificationUserStatus.user_id == current_user.id
        )
        res = await session.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            record.is_read = True
            record.read_at = now
        else:
            session.add(NotificationUserStatus(
                notification_id=nid, user_id=current_user.id, is_read=True, read_at=now
            ))

    await session.commit()
    return {"message": f"Marked {len(notification_ids)} as read"}
