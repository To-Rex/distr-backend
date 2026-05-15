from fastapi import APIRouter, Query

from apps.activity.services.activity_service import ActivityService
from apps.app_store.utils.response import success_response

router = APIRouter(
    prefix="/activity",
    tags=["Activity"],
)


@router.get("")
def get_activities(lang: str = Query("uz", regex="^(uz|ru|en)$")):
    activities = ActivityService.get_list(lang)
    return success_response(activities)
