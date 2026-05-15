from apps.app_store.repositories.app_repository import AppRepository
from apps.app_store.repositories.category_repository import CategoryRepository
from apps.app_store.repositories.version_repository import VersionRepository


class StatsService:
    @staticmethod
    def get_stats() -> dict:
        apps = AppRepository.get_all()
        versions = VersionRepository.get_all()
        categories = CategoryRepository.get_all()
        total_downloads = sum(a.get("totalDownloads", 0) for a in apps)

        return {
            "totalApps": len(apps),
            "totalVersions": len(versions),
            "totalDownloads": total_downloads,
            "totalCategories": len(categories),
        }
