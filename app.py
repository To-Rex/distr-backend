import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import jinja2
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
from config.db_setup import apply_and_reconnect, test_connection, get_current_db_params
from apps.routes import main_router
from apps.app_store.routes import app_store_router
from apps.app_store.config import EXPORTS_DIR as APPSTORE_EXPORTS_DIR
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
    try:
        await create_all_tables()
        app.state.db_connected = True
        print("[+] All tables created")
    except Exception as e:
        app.state.db_connected = False
        print(f"[!] Database connection failed: {e}")
        print("[!] Serving database setup page at http://0.0.0.0:8002/setup")

    # 2. AppStore default admin seeding (only if DB connected)
    if app.state.db_connected:
        try:
            from apps.app_store.services.user_service import UserService

            UserService.ensure_default_admin()
            print("[+] AppStore default admin ensured")
        except Exception as e:
            print(f"[!] Failed to seed AppStore default admin: {e}")

    # 3. Firebase logic (Check if already initialized to prevent crash)
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
app.state.db_connected = False


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


@app.get("/")
async def redirect_root(request: Request):
    if not request.app.state.db_connected:
        return RedirectResponse(url="/setup")
    return RedirectResponse(url="https://dms.mxsoft.uz/")

# ---- Database Setup Routes (available even when DB is down) ----
_SETUP_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
_setup_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_SETUP_TEMPLATES_DIR),
    autoescape=True,
)


class DBSettings(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database: str


@app.get("/setup")
async def setup_page(request: Request):
    params = get_current_db_params()
    template = _setup_jinja_env.get_template("setup_db.html")
    html = template.render({
        "request": request,
        "host": params.get("host", ""),
        "port": params.get("port", "5432"),
        "user": params.get("user", "postgres"),
        "password": params.get("password", ""),
        "database": params.get("database", ""),
    })
    return HTMLResponse(content=html)


@app.post("/setup/test")
async def setup_test(settings: DBSettings):
    ok, err = await test_connection(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        database=settings.database,
    )
    return JSONResponse(
        {"success": True} if ok else {"success": False, "error": err}
    )


@app.post("/setup/save")
async def setup_save(settings: DBSettings, request: Request):
    try:
        saved, reconnected, db_url, error = await apply_and_reconnect(
            host=settings.host,
            port=settings.port,
            user=settings.user,
            password=settings.password,
            database=settings.database,
            admin_obj=admin,
        )
        if not saved:
            return JSONResponse({"success": False, "error": error or "Failed to save"})
        if reconnected:
            request.app.state.db_connected = True
            return JSONResponse(
                {"success": True, "reconnected": True, "db_url": db_url}
            )
        return JSONResponse(
            {"success": True, "reconnected": False, "error": error}
        )
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


_last_health_check: float = 0.0
_HEALTH_CHECK_INTERVAL = 5


class DBSetupMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        global _last_health_check
        import time as _time

        now = _time.monotonic()
        if now - _last_health_check > _HEALTH_CHECK_INTERVAL:
            _last_health_check = now
            try:
                from config.database import check_db_alive
                alive = await check_db_alive()
                request.app.state.db_connected = alive
            except Exception:
                request.app.state.db_connected = False

        path = request.url.path
        db_ok = request.app.state.db_connected
        is_setup = path.startswith("/setup")
        is_excluded = any(path.startswith(p) for p in ("/static", "/favicon.ico"))

        if db_ok and is_setup:
            return RedirectResponse(url="/", status_code=302)

        if not db_ok and not is_setup and not is_excluded:
            return RedirectResponse(url="/setup", status_code=302)

        return await call_next(request)


app.add_middleware(DBSetupMiddleware)

# admin
app.include_router(main_router)

# appstore service
app.include_router(app_store_router)

from sqladmin.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

print(f"Current Directory: {os.getcwd()}")
print(f"Media folder exists: {os.path.exists('media')}")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/appstore/exports",
          StaticFiles(directory=str(APPSTORE_EXPORTS_DIR)), name="appstore-exports")

if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv
    load_dotenv()
    PORT = int(os.getenv("PORT", "8002"))

    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=True)
