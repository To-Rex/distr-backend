import logging
import sys
from datetime import datetime
from sqlalchemy.orm import contains_eager
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from firebase_admin import messaging
from apps.notification.models import Notification, NotificationUserStatus

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
from apps.notification.schemas import (
    AdminNotificationBy1cIdCreate,
    AdminNotificationCreate,
    NotificationCreate,
    NotificationResponse,
    SecurityKeyNotificationCreate,
    NotificationUpdate,
    NotificationUserStatusResponse,
    UnreadCountResponse,
)
from apps.user.models import User, UserType
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
        effective_company_id = notification_data.company_id

        # 1. Validate Security Key
        if notification_data.security_key:
            res = await session.execute(select(SecurityKey).where(SecurityKey.key == notification_data.security_key))
            security_key_obj = res.scalar_one_or_none()
            if not security_key_obj:
                raise HTTPException(
                    status_code=400, detail="Invalid security key")

            effective_company_id = security_key_obj.company_id

            if notification_data.company_id is not None and security_key_obj.company_id != notification_data.company_id:
                raise HTTPException(
                    status_code=400, detail="Security key mismatch for company")

        # 2. Validate Company
        if effective_company_id is not None:
            res = await session.execute(select(Company).where(Company.id == effective_company_id))
            if not res.scalar_one_or_none():
                raise HTTPException(
                    status_code=404, detail="Company not found")

        new_notification = Notification(
            **notification_data.model_dump(exclude={'security_key', 'users_1c_id'}))
        new_notification.company_id = effective_company_id
        session.add(new_notification)
        await session.commit()
        await session.refresh(new_notification)

        target_1c_ids = []
        if notification_data.users_1c_id:
            target_1c_ids = notification_data.users_1c_id
        elif notification_data.user_1c_id is not None:
            target_1c_ids = [notification_data.user_1c_id]

        sent_count = 0
        skip_no_user = 0
        skip_no_token = 0
        fail_count = 0

        for user_1c_id in target_1c_ids:
            query = select(User).where(User.user_1c_id == user_1c_id)
            if effective_company_id is not None:
                query = query.where(User.company_id == effective_company_id)
            result = await session.execute(query)
            target_users = result.scalars().all()

            if not target_users:
                skip_no_user += 1
                logger.warning("FCM skip: user_1c_id=%s not found", user_1c_id)
                continue

            for target_user in target_users:
                if not target_user.fcm_token:
                    skip_no_token += 1
                    logger.warning("FCM skip: user_1c_id=%s (user_id=%s) has no fcm_token", user_1c_id, target_user.id)
                    continue

                try:
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=new_notification.title,
                            body=new_notification.message
                        ),
                        token=target_user.fcm_token
                    )
                    response = messaging.send(message)
                    sent_count += 1
                    logger.info("FCM sent: user_1c_id=%s, user_id=%s, title=%s, fcm_response=%s", user_1c_id, target_user.id, new_notification.title, response)
                except Exception as fcm_error:
                    fail_count += 1
                    logger.error("FCM failed: user_1c_id=%s, user_id=%s, title=%s, error=%s", user_1c_id, target_user.id, new_notification.title, fcm_error)

        logger.info("FCM summary: notification_id=%s, total=%s, sent=%s, no_user=%s, no_token=%s, failed=%s",
                     new_notification.id, len(target_1c_ids), sent_count, skip_no_user, skip_no_token, fail_count)

        return new_notification
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"Database error: {str(e)}")


@router.post("/send-to-user", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_notification_to_user(
    notification_data: AdminNotificationCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type not in [UserType.SUPERADMIN, UserType.ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can send notifications to specific users")

    target_user = await session.get(User, notification_data.user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    new_notification = Notification(
        title=notification_data.title,
        message=notification_data.message,
        date=notification_data.date,
        author=notification_data.author,
        company_id=target_user.company_id,
        user_1c_id=target_user.user_1c_id,
        user_type=target_user.user_type.value if target_user.user_type else None,
    )
    session.add(new_notification)
    await session.commit()
    await session.refresh(new_notification)

    status_record = NotificationUserStatus(
        notification_id=new_notification.id,
        user_id=target_user.id,
        is_read=False,
    )
    session.add(status_record)
    await session.commit()

    if target_user.fcm_token:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=new_notification.title,
                    body=new_notification.message
                ),
                token=target_user.fcm_token
            )
            response = messaging.send(message)
            logger.info("FCM sent: user_id=%s, title=%s, fcm_response=%s", target_user.id, new_notification.title, response)
        except Exception as fcm_error:
            logger.error("FCM failed: user_id=%s, title=%s, error=%s", target_user.id, new_notification.title, fcm_error)

    return new_notification


@router.post("/send-to-user-1c", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_notification_to_user_by_1c(
    notification_data: AdminNotificationBy1cIdCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    if current_user.user_type not in [UserType.SUPERADMIN, UserType.ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can send notifications to specific users")

    query = select(User).where(User.user_1c_id == notification_data.user_1c_id)
    if notification_data.company_id is not None:
        query = query.where(User.company_id == notification_data.company_id)

    result = await session.execute(query)
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    new_notification = Notification(
        title=notification_data.title,
        message=notification_data.message,
        date=notification_data.date,
        author=notification_data.author,
        company_id=target_user.company_id,
        user_1c_id=target_user.user_1c_id,
        user_type=target_user.user_type.value if target_user.user_type else None,
    )
    session.add(new_notification)
    await session.commit()
    await session.refresh(new_notification)

    status_record = NotificationUserStatus(
        notification_id=new_notification.id,
        user_id=target_user.id,
        is_read=False,
    )
    session.add(status_record)
    await session.commit()

    if target_user.fcm_token:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=new_notification.title,
                    body=new_notification.message
                ),
                token=target_user.fcm_token
            )
            response = messaging.send(message)
            logger.info("FCM sent: user_1c_id=%s, title=%s, fcm_response=%s", target_user.user_1c_id, new_notification.title, response)
        except Exception as fcm_error:
            logger.error("FCM failed: user_1c_id=%s, title=%s, error=%s", target_user.user_1c_id, new_notification.title, fcm_error)

    return new_notification


@router.post("/send-by-key", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_notification_by_key(
    notification_data: SecurityKeyNotificationCreate,
    session: AsyncSession = Depends(get_async_session),
):
    res = await session.execute(select(SecurityKey).where(SecurityKey.key == notification_data.security_key))
    security_key_obj = res.scalar_one_or_none()
    if not security_key_obj:
        raise HTTPException(status_code=400, detail="Invalid security key")

    result = await session.execute(select(User).where(User.user_1c_id == notification_data.user_1c_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    new_notification = Notification(
        title=notification_data.title,
        message=notification_data.message,
        date=notification_data.date,
        author=notification_data.author,
        company_id=target_user.company_id,
        user_1c_id=target_user.user_1c_id,
        user_type=target_user.user_type.value if target_user.user_type else None,
    )
    session.add(new_notification)
    await session.commit()
    await session.refresh(new_notification)

    status_record = NotificationUserStatus(
        notification_id=new_notification.id,
        user_id=target_user.id,
        is_read=False,
    )
    session.add(status_record)
    await session.commit()

    if target_user.fcm_token:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=new_notification.title,
                    body=new_notification.message
                ),
                token=target_user.fcm_token
            )
            response = messaging.send(message)
            logger.info("FCM sent: user_1c_id=%s, title=%s, fcm_response=%s", target_user.user_1c_id, new_notification.title, response)
        except Exception as fcm_error:
            logger.error("FCM failed: user_1c_id=%s, title=%s, error=%s", target_user.user_1c_id, new_notification.title, fcm_error)

    return new_notification


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
