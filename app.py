import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqladmin.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from apps.user.admin import UserAdmin
from apps.company.admin import CompanyAdmin, SecurityKeyAdmin
from apps.location.admin import LocationAdmin
from apps.app_version.admin import AppAdmin, VersionAdmin
from apps.working_session_tracking.admin import WorkingSessionAdmin
from apps.notification.admin import NotificationAdmin, NotificationUserStatusAdmin
from apps.alembic_version.admin import AlembicVersionAdmin
from config.dashboard_security import authentication_backend
from config.database import create_all_tables, engine
from apps.routes import main_router
from apps.app_store.routes import app_store_router
from apps.app_store.config import UPLOADS_DIR as APPSTORE_UPLOADS_DIR, EXPORTS_DIR as APPSTORE_EXPORTS_DIR
from sqladmin import Admin
import firebase_admin
from firebase_admin import credentials


import mimetypes

mimetypes.add_type(
    'application/vnd.android.package-archive',
    '.apk'
)


# @asynccontextmanager
# async def create_db(app: FastAPI):
#     await create_all_tables()
#     print("[+] All tables created")
#     yield

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Database logic
    await create_all_tables()
    print("[+] All tables created")

    # 2. Firebase logic (Check if already initialized to prevent crash)
    if not firebase_admin._apps:
        cred = credentials.Certificate("config/config_notification.json")
        firebase_admin.initialize_app(cred)
        print("[+] Firebase Admin initialized")

    yield
    # Any shutdown logic goes here (optional)

app = FastAPI(
    title="MXSoft Distr Dashboard",
    description="MXSoft User Controlling Dashboard",
    version="1.0.0",
    lifespan=lifespan,
)
class CORSAnyOriginMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method == "OPTIONS":
            response = Response()
        else:
            response = await call_next(request)

        origin = request.headers.get("origin", "*")
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response

app.add_middleware(CORSAnyOriginMiddleware)

# cred = credentials.Certificate("config/config_notification.json")
# firebase_admin.initialize_app(cred)


admin = Admin(
    app,
    engine,
    base_url="/admin",
    authentication_backend=authentication_backend,
)

# Add it to the dashboard
admin.add_view(UserAdmin)
admin.add_view(CompanyAdmin)
admin.add_view(SecurityKeyAdmin)
admin.add_view(LocationAdmin)
admin.add_view(AppAdmin)
admin.add_view(VersionAdmin)
admin.add_view(WorkingSessionAdmin)
admin.add_view(NotificationAdmin)
admin.add_view(NotificationUserStatusAdmin)
admin.add_view(AlembicVersionAdmin)

# @app.get("/")
# async def redirect_root():
#     return RedirectResponse(url="https://dms.mxsoft.uz/")

# admin
app.include_router(main_router)

# appstore service
app.include_router(app_store_router)

templates = Jinja2Templates(directory="templates")

print(f"Current Directory: {os.getcwd()}")
print(f"Media folder exists: {os.path.exists('media')}")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/appstore/uploads", StaticFiles(directory=str(APPSTORE_UPLOADS_DIR)), name="appstore-uploads")
app.mount("/appstore/exports", StaticFiles(directory=str(APPSTORE_EXPORTS_DIR)), name="appstore-exports")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
