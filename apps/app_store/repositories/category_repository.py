from typing import Optional

from apps.app_store.config import CATEGORIES_JSON
from apps.app_store.utils.minio_json_db import MinioJsonDB

DEFAULT_CATEGORIES = [
    {"id": "productivity", "name": "Productivity", "labelUz": "Samaradorlik"},
    {"id": "communication", "name": "Communication", "labelUz": "Aloqa"},
    {"id": "development", "name": "Development", "labelUz": "Dasturlash"},
    {"id": "security", "name": "Security", "labelUz": "Xavfsizlik"},
    {"id": "media", "name": "Media", "labelUz": "Media"},
    {"id": "utilities", "name": "Utilities", "labelUz": "Yordamchi"},
    {"id": "finance", "name": "Finance", "labelUz": "Moliya"},
    {"id": "education", "name": "Education", "labelUz": "Ta'lim"},
]


class CategoryRepository:
    @staticmethod
    def get_all() -> list[dict]:
        categories = MinioJsonDB.read(CATEGORIES_JSON)
        if not categories:
            MinioJsonDB.write(CATEGORIES_JSON, DEFAULT_CATEGORIES)
            return list(DEFAULT_CATEGORIES)
        return categories

    @staticmethod
    def get_by_id(cat_id: str) -> Optional[dict]:
        return MinioJsonDB.read_one(CATEGORIES_JSON, lambda c: c["id"] == cat_id)
