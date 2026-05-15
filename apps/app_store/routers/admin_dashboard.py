from fastapi import APIRouter, Depends

from apps.app_store.middleware.auth import get_current_user
from apps.app_store.services.dashboard_service import DashboardService
from apps.app_store.utils.response import success_response

router = APIRouter(prefix="/admin", tags=["AppStore Admin Dashboard"])


@router.get("/dashboard")
def admin_dashboard(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "admin":
        data = DashboardService.get_admin_dashboard()
    else:
        data = DashboardService.get_publisher_dashboard(current_user["sub"])
    return success_response(data)
