import logging
from datetime import datetime, time
import asyncio
from typing import List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Query, Depends, HTTPException
from starlette.websockets import WebSocket, WebSocketDisconnect

from apps.location.models import Location
from apps.location.schemas import LocationRead, LocationCreate, LocationUpdate, LocationBatchRequest
from apps.user.models import User, UserType
from config.database import get_async_session, async_session_maker
from managers.c2_manager import c2_manager
from apps.user.di import get_current_user, get_current_user_by_token

router = APIRouter(
    prefix="/locations",
    tags=["User Locations"],
)


@router.post("/", response_model=LocationRead, status_code=201)
async def create_location(
    location_data: LocationCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    # Verify user exists
    result = await session.execute(select(User).where(User.id == location_data.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_location = Location(**location_data.model_dump())
    session.add(new_location)
    await session.commit()
    await session.refresh(new_location)
    return new_location


@router.post("/batch", status_code=201)
async def batch_create_locations(
    batch_data: LocationBatchRequest,
    current_user: User = Depends(get_current_user_by_token),
):
    allowed_roles = ["AGENT", "DELIVERER", "MERCHANDISER", "SUPERVISOR", "VENDOR_AGENT"]
    if current_user.user_type.value not in allowed_roles:
        raise HTTPException(status_code=403, detail="Only field agents can upload locations")

    count = 0
    for item in batch_data.locations:
        loc_dict = item.model_dump()
        data = {
            "action": "update_location",
            "location": {
                "latitude": loc_dict["latitude"],
                "longitude": loc_dict["longitude"],
                "device_name": loc_dict.get("device_name") or "Unknown",
            },
            "speed": loc_dict.get("speed", 0.0),
            "bearing": loc_dict.get("bearing", 0.0),
            "accuracy": loc_dict.get("accuracy", 0.0),
            "altitude": loc_dict.get("altitude", 0.0),
            "timestamp": loc_dict.get("timestamp") or datetime.now().isoformat(),
        }
        await c2_manager.update_location(current_user.id, data)
        count += 1

    return {"status": "success", "count": count}


@router.get("/", response_model=List[LocationRead])
async def list_all_locations(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
    is_active: Optional[bool] = None,
    user_id: Optional[int] = None,
):
    query = select(Location)
    if is_active is not None:
        query = query.where(Location.is_active == is_active)
    if user_id is not None:
        query = query.where(Location.user_id == user_id)
    query = query.order_by(Location.created_at.desc())
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/{location_id}", response_model=LocationRead)
async def get_location(
    location_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.put("/{location_id}", response_model=LocationRead)
async def update_location(
    location_id: int,
    location_data: LocationUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    update_data = location_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)

    await session.commit()
    await session.refresh(location)
    return location


@router.delete("/{location_id}", status_code=204)
async def delete_location(
    location_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    result = await session.execute(select(Location).where(Location.id == location_id))
    location = result.scalar_one_or_none()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    await session.delete(location)
    await session.commit()


@router.get("/user-history/{user_id}", response_model=List[LocationRead])
async def get_user_location_history(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user_by_token),
):
    # Check if user exists
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Define the time range for "Today"
    today_start = datetime.combine(datetime.now().date(), time.min)
    try:
        query = (
            select(Location)
            .where(
                Location.user_id == user_id,
                Location.created_at >= today_start
            )
            .order_by(Location.created_at.asc())
        )
        result = await session.execute(query)
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("C2Manager")


@router.websocket("/ws/admvs")
async def unified_websocket_handler(
    websocket: WebSocket,
    token: str | None = Query(None),
):
    authenticated, user = await authenticate_websocket(websocket, token)
    if not authenticated:
        return

    await c2_manager.connect(user, websocket)

    HEARTBEAT_INTERVAL = 40.0

    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(), timeout=HEARTBEAT_INTERVAL
                )

                action = data.get("action")

                if action == "update_location":
                    await c2_manager.update_location(user.id, data)

            except asyncio.TimeoutError:
                try:
                    await websocket.send_json({"action": "ping"})
                except Exception:
                    break

    except WebSocketDisconnect:
        logger.info(f"[WS] Disconnect: {user.id}")
    except Exception as e:
        logger.error(f"[WS] Error: {e}")
    finally:
        await c2_manager.disconnect(user.id)


async def authenticate_websocket(
    websocket: WebSocket, token: str | None
) -> tuple[bool, str | None]:
    if not token:
        await websocket.close(code=401, reason="Missing token")
        return False, None

    async with async_session_maker() as session:
        try:
            user = await get_current_user(token, session)
        except Exception:
            await websocket.close(code=401, reason="Invalid token")
            return False, None
    return True, user