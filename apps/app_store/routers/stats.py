from fastapi import APIRouter

from apps.app_store.services.stats_service import StatsService
from apps.app_store.utils.response import success_response

router = APIRouter(prefix="", tags=["AppStore Stats"])


@router.get("/stats")
def get_stats():
    stats = StatsService.get_stats()
    return success_response(stats)
