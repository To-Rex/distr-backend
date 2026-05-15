from fastapi import APIRouter

from apps.app_store.routers import (
    auth,
    apps,
    admin_apps,
    admin_versions,
    admin_screenshots,
    admin_dashboard,
    admin_users,
    upload,
    categories,
    stats,
    data_export,
)

app_store_router = APIRouter(prefix="/appstore")

app_store_router.include_router(auth.router)
app_store_router.include_router(apps.router)
app_store_router.include_router(admin_apps.router)
app_store_router.include_router(admin_versions.router)
app_store_router.include_router(admin_screenshots.router)
app_store_router.include_router(admin_dashboard.router)
app_store_router.include_router(admin_users.router)
app_store_router.include_router(upload.router)
app_store_router.include_router(categories.router)
app_store_router.include_router(stats.router)
app_store_router.include_router(data_export.router)


@app_store_router.get("/health")
def health_check():
    return {"status": "ok", "service": "appstore"}
