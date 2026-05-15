from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    UploadFile,
    File,
    Form,
    status,
)

from apps.app_store.middleware.auth import get_current_user
from apps.app_store.repositories.app_repository import AppRepository
from apps.app_store.repositories.user_repository import UserRepository
from apps.app_store.services.app_service import AppService
from apps.app_store.services.upload_service import UploadService
from apps.app_store.utils.response import success_response, error_response, paginated_response

router = APIRouter(prefix="/admin", tags=["AppStore Admin Apps"])


def _check_app_access(app_id: str, current_user: dict) -> dict:
    app = AppRepository.get_by_id(app_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Ilova topilmadi"),
        )
    if current_user["role"] != "admin" and app["createdBy"] != current_user["sub"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response("Bu ilovani ko'rish huquqingiz yo'q"),
        )
    return app


@router.get("/apps")
def admin_get_apps(
    page: int = 1,
    limit: int = 20,
    published: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
):
    apps, total = AppService.get_admin_list(
        user_id=current_user["sub"],
        user_role=current_user["role"],
        page=page,
        limit=limit,
        published=published,
    )
    return paginated_response(apps, page, limit, total)


@router.get("/apps/{app_id}")
def admin_get_app(app_id: str, current_user: dict = Depends(get_current_user)):
    _check_app_access(app_id, current_user)
    app = AppService.get_admin_by_id(app_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Ilova topilmadi"),
        )
    return success_response(app)


@router.post("/apps", status_code=status.HTTP_201_CREATED)
async def admin_create_app(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    form = await request.form()
    name = form.get("name")
    developer = form.get("developer", "")
    short_description = form.get("shortDescription")
    category = form.get("category")

    if not developer or not str(developer).strip():
        creator = UserRepository.get_by_id(current_user["sub"])
        developer = creator["displayName"] if creator else current_user["sub"]

    if not all([name, short_description, category]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("Majburiy maydonlar to'ldirilmagan"),
        )

    description = form.get("description", "")
    tags_str = form.get("tags", "")
    published_raw = form.get("published", "false")
    published = str(published_raw).lower() == "true"

    icon_url = ""
    icon_file = form.get("icon")
    if icon_file and hasattr(icon_file, "read"):
        content = await icon_file.read()
        result = UploadService.upload_icon(content, icon_file.filename)
        icon_url = result["url"]

    app = AppService.create_app(
        user_id=current_user["sub"],
        name=str(name),
        developer=str(developer),
        short_description=str(short_description),
        category=str(category),
        description=str(description) if description else "",
        tags_str=str(tags_str) if tags_str else "",
        icon=icon_url,
        published=published,
    )
    return success_response(app)


@router.put("/apps/{app_id}")
async def admin_update_app(
    app_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    _check_app_access(app_id, current_user)

    form = await request.form()
    updates = {}

    simple_fields = ["name", "developer", "shortDescription", "description", "category"]
    for field in simple_fields:
        val = form.get(field)
        if val is not None:
            updates[field] = str(val)

    tags = form.get("tags")
    if tags is not None:
        updates["tags"] = [t.strip() for t in str(tags).split(",") if t.strip()]

    published = form.get("published")
    if published is not None:
        updates["published"] = str(published).lower() == "true"

    icon_file = form.get("icon")
    if icon_file and hasattr(icon_file, "read"):
        content = await icon_file.read()
        result = UploadService.upload_icon(content, icon_file.filename)
        updates["icon"] = result["url"]

    app = AppService.update_app(app_id, **updates)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Ilova topilmadi"),
        )
    return success_response(app)


@router.delete("/apps/{app_id}")
def admin_delete_app(app_id: str, current_user: dict = Depends(get_current_user)):
    _check_app_access(app_id, current_user)
    AppService.delete_app(app_id)
    return success_response(message="Ilova muvaffaqiyatli o'chirildi")


@router.patch("/apps/{app_id}/toggle-publish")
def admin_toggle_publish(app_id: str, current_user: dict = Depends(get_current_user)):
    _check_app_access(app_id, current_user)
    result = AppService.toggle_publish(app_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Ilova topilmadi"),
        )
    return success_response(result)
