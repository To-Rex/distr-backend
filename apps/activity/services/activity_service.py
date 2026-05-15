from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from apps.app_store.utils.json_db import JsonDB

ACTIVITIES_JSON = Path(__file__).resolve().parent.parent / "data" / "activities.json"
MAX_ACTIVITIES = 6


class ActivityService:
    @staticmethod
    def log(action: str, messages: dict[str, str]) -> dict:
        activities = JsonDB.read(ACTIVITIES_JSON)
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": int(datetime.now(timezone.utc).timestamp() * 1000),
            "action": action,
            "message": messages,
            "created_at": now,
        }
        activities.insert(0, record)
        if len(activities) > MAX_ACTIVITIES:
            activities = activities[:MAX_ACTIVITIES]
        JsonDB.write(ACTIVITIES_JSON, activities)
        return record

    @staticmethod
    def get_list(lang: str = "uz") -> list[dict]:
        activities = JsonDB.read(ACTIVITIES_JSON)
        result = []
        for a in activities:
            msg = a.get("message", {})
            result.append({
                "id": a["id"],
                "action": a["action"],
                "message": msg.get(lang, msg.get("uz", "")),
                "created_at": a["created_at"],
            })
        return result

    @staticmethod
    def clear():
        JsonDB.write(ACTIVITIES_JSON, [])
