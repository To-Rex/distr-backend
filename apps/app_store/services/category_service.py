from apps.app_store.repositories.app_repository import AppRepository
from apps.app_store.repositories.category_repository import CategoryRepository


class CategoryService:
    @staticmethod
    def get_all() -> list[dict]:
        counts = AppRepository.get_by_category()
        categories = CategoryRepository.get_all()
        result = []
        for cat in categories:
            result.append(
                {
                    "id": cat["id"],
                    "name": cat["name"],
                    "labelUz": cat.get("labelUz", cat["name"]),
                    "appCount": counts.get(cat["name"], 0),
                }
            )
        return result
