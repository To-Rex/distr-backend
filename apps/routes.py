from fastapi import APIRouter

from .activity import routes as activity_routes
from .alembic_version import routes as alembic_version_routes
from .app_version import routes as app_version_routes
from .company import routes as company_routes
from .device import routes as device_routes
from .location import routes as location_routes
from .notification import routes as notification_routes
from .system_monitor import routes as system_monitor_routes
from .user import routes as user_routes
from .user import user_manager_routes as user_manager_routes
from .working_session_tracking import routes as working_session_routes
from .database_backup import routes as database_backup_routes

main_router = APIRouter(
    prefix="/api/v1",
)

main_router.include_router(user_routes.router)
main_router.include_router(user_manager_routes.router)
main_router.include_router(location_routes.router)
main_router.include_router(app_version_routes.router)
main_router.include_router(working_session_routes.router)
main_router.include_router(notification_routes.router)
main_router.include_router(company_routes.router)
main_router.include_router(device_routes.router)
main_router.include_router(system_monitor_routes.router)
main_router.include_router(activity_routes.router)
main_router.include_router(alembic_version_routes.router)
main_router.include_router(database_backup_routes.router)
