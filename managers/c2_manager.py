

from typing import Dict, List
from sqlalchemy import select, desc
from starlette.websockets import WebSocket, WebSocketDisconnect

from apps.user.models import User, UserType
from apps.location.models import Location
from config.database import async_session_maker

import json
from typing import Dict, List, Any
from sqlalchemy import select, desc
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum


import json
from typing import Dict, List, Any
from sqlalchemy import select, desc
from fastapi import WebSocket


import asyncio
import logging
from typing import Dict, List, Any, Optional
from fastapi import WebSocket
from sqlalchemy import select, desc
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("C2Manager")


class C2Manager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.parent_map: Dict[int, Optional[int]] = {}
        self.user_roles: Dict[int, str] = {}

    # ─────────────────────────────────────────────
    # CONNECT
    # ─────────────────────────────────────────────
    async def connect(self, user: Any, websocket: WebSocket):
        await websocket.accept()

        self.active_connections[user.id] = websocket
        self.parent_map[user.id] = user.manager_id
        self.user_roles[user.id] = user.user_type.value

        logger.info(
            f"[CONNECT] User {user.id} ({user.user_type.value}) | parent={user.manager_id}"
        )
        logger.info(
            f"[STATE]   active={list(self.active_connections.keys())} | parent_map={self.parent_map}"
        )

        # Send initial list to bosses
        if user.user_type.value in ["MANAGER", "SUPERVISOR", "ADMIN"]:
            users_list = await self._get_scoped_users_list(user)
            await self._safe_send_json(websocket, {
                "action": "all_admvs",
                "users": users_list
            })

        # Tell bosses this user just came online
        await self._notify_hierarchy(user.id, {
            "action": "status_update",
            "user_id": user.id,
            "status": "online"
        })

    # ─────────────────────────────────────────────
    # DISCONNECT
    # ─────────────────────────────────────────────
    async def disconnect(self, user_id: int):
        self.active_connections.pop(user_id, None)
        logger.info(f"[DISCONNECT] User {user_id}")

        await self._notify_hierarchy(user_id, {
            "action": "status_update",
            "user_id": user_id,
            "status": "offline"
        })

    async def update_location(self, sender_id: int, data: dict):
        role = self.user_roles.get(sender_id, "")
        loc = data.get("location", {})
        print(loc)

        # Only Agents, Deliverers, and Supervisors can send location
        allowed_roles = ["AGENT", "DELIVERER", 
                         "MERCHANDISER", "SUPERVISOR", "VENDOR_AGENT"]
        if role not in allowed_roles:
            logger.warning(
                f"[LOCATION] User {sender_id} ({role}) tried to send location — ignored")
            return

        # Fetch user from DB and serialize manually
        user_data = None
        async with async_session_maker() as session:
            res = await session.execute(select(User).where(User.id == sender_id))
            user = res.scalar_one_or_none()
            if user:
                user_data = {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.user_type.value,
                    "user_1c_id": user.user_1c_id,
                    "phone_number": user.phone_number,
                }

        payload = {
            "action": "update_location",
            "user": user_data,          # ← plain dict, not ORM object
            "role": role,
            "location": {
                "latitude": loc.get("latitude"),
                "longitude": loc.get("longitude"),
                "device_name": loc.get("device_name", "Unknown"),
            },
            "speed": data.get("speed", 0.0),
            "bearing": data.get("bearing", 0.0),
            "accuracy": data.get("accuracy", 0),
            "altitude": data.get("altitude", 0.0),
            "timestamp": data.get("timestamp") or datetime.now().isoformat(),
        }

        logger.info(f"[LOCATION] {role} {sender_id} → bubbling up")

        asyncio.create_task(self._save_location_to_db(sender_id, loc))
        await self._notify_hierarchy(sender_id, payload)

    # ─────────────────────────────────────────────
    # CORE: RECURSIVE BUBBLE-UP
    # ─────────────────────────────────────────────
    async def _notify_hierarchy(self, sender_id: int, payload: dict):
        """
        Climbs the manager_id tree recursively.
        Falls back to DB if parent not cached (fixes connection-order bug).
        """
        parent_id = self.parent_map.get(sender_id)

        # Fallback: load from DB if not cached
        if parent_id is None and sender_id not in self.parent_map:
            parent_id = await self._load_parent_from_db(sender_id)
            if parent_id is not None:
                self.parent_map[sender_id] = parent_id

        if not parent_id:
            logger.info(f"[BUBBLE] {sender_id} → top of hierarchy, done.")
            return

        if parent_id in self.active_connections:
            logger.info(
                f"[PUSH] {sender_id} ({self.user_roles.get(sender_id, '?')}) "
                f"→ {parent_id} ({self.user_roles.get(parent_id, '?')})"
            )
            await self._safe_send_json(self.active_connections[parent_id], payload)
        else:
            logger.info(f"[SKIP] Parent {parent_id} is offline.")

        # Recurse one level higher
        await self._notify_hierarchy(parent_id, payload)

    async def _load_parent_from_db(self, user_id: int) -> Optional[int]:
        try:
            async with async_session_maker() as session:
                res = await session.execute(
                    select(User.manager_id).where(User.id == user_id)
                )
                return res.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[DB] Could not load parent for {user_id}: {e}")
            return None

    # ─────────────────────────────────────────────
    # INITIAL LIST FOR MANAGERS / SUPERVISORS
    # ─────────────────────────────────────────────
    async def _get_scoped_users_list(self, boss: Any) -> List[dict]:
        async with async_session_maker() as session:
            subordinates = []

            if boss.user_type.value == "MANAGER":
                # Supervisors directly under this Manager
                res = await session.execute(
                    select(User).where(User.manager_id == boss.id)
                )
                sups = res.scalars().all()
                subordinates.extend(sups)

                # Agents/Deliverers under those Supervisors
                sup_ids = [s.id for s in sups]
                if sup_ids:
                    res2 = await session.execute(
                        select(User).where(User.manager_id.in_(sup_ids))
                    )
                    subordinates.extend(res2.scalars().all())

            elif boss.user_type.value == "SUPERVISOR":
                # Only direct subordinates (Agents, Deliverers)
                res = await session.execute(
                    select(User).where(User.manager_id == boss.id)
                )
                subordinates.extend(res.scalars().all())

            return [await self._format_user_node(session, s) for s in subordinates]

    async def _format_user_node(self, session, user: Any) -> dict:
        loc_res = await session.execute(
            select(Location)
            .where(Location.user_id == user.id)
            .order_by(desc(Location.created_at))
            .limit(1)
        )
        last_loc = loc_res.scalar_one_or_none()

        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.user_type.value,
            "user_1c_id": user.user_1c_id,
            "status": "online" if user.id in self.active_connections else "offline",
            "last_location": {
                "latitude": last_loc.latitude if last_loc else 0.0,
                "longitude": last_loc.longitude if last_loc else 0.0,
                "timestamp": last_loc.created_at.isoformat() if last_loc else None,
            },
        }

    # ─────────────────────────────────────────────
    # DB SAVE
    # ─────────────────────────────────────────────
    async def _save_location_to_db(self, user_id: int, loc: dict):
        async with async_session_maker() as session:
            try:
                new_loc = Location(
                    user_id=user_id,
                    latitude=loc.get("latitude"),
                    longitude=loc.get("longitude"),
                    device_name=loc.get("device_name")
                )
                session.add(new_loc)
                await session.commit()
            except Exception as e:
                logger.error(f"[DB] Save failed for {user_id}: {e}")

    async def _safe_send_json(self, websocket: WebSocket, data: dict):
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.warning(f"[SEND] Failed: {e}")


c2_manager = C2Manager()
