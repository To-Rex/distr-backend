from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status

from apps.app_store.config import SCREENSHOTS_DIR
from apps.app_store.middleware.auth import get_current_user
from apps.app_store.repositories.app_repository import AppRepository
from apps.app_store.services.upload_service import UploadService
from apps.app_store.utils.response import success_response, error_response

router = APIRouter(prefix="/admin", tags=["AppStore Admin Screenshots"])


def _check_app_access(app_id: str, current_user: dict):
    app = AppRepository.get_by_id(app_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Ilova topilmadi"),
        )
    if current_user["role"] != "admin" and app["createdBy"] != current_user["sub"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response("Bu ilovani tahrirlash huquqingiz yo'q"),
        )
    return app


def _delete_screenshot_file(screenshot_url: str):
    filename = screenshot_url.split("/")[-1]
    file_path = SCREENSHOTS_DIR / filename
    if file_path.exists():
        file_path.unlink()


@router.post("/apps/{app_id}/screenshots")
async def admin_upload_screenshots(
    app_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    _check_app_access(app_id, current_user)

    form = await request.form()
    uploaded_urls = []

    for key in form:
        if key == "screenshots":
            files = form.getlist(key)
            for f in files:
                if hasattr(f, "read"):
                    content = await f.read()
                    result = UploadService.upload_screenshot(content, f.filename)
                    uploaded_urls.append(result["url"])

    if not uploaded_urls:
        single = form.get("screenshots")
        if single and hasattr(single, "read"):
            content = await single.read()
            result = UploadService.upload_screenshot(content, single.filename)
            uploaded_urls.append(result["url"])

    if not uploaded_urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("Yuklash uchun skrinshot fayllari topilmadi"),
        )

    app = AppRepository.get_by_id(app_id)
    existing = app.get("screenshots", [])
    existing.extend(uploaded_urls)
    AppRepository.update(app_id, {"screenshots": existing})

    return success_response({"screenshots": existing, "added": len(uploaded_urls)})


@router.delete("/apps/{app_id}/screenshots/{index}")
def admin_delete_screenshot(
    app_id: str,
    index: int,
    current_user: dict = Depends(get_current_user),
):
    _check_app_access(app_id, current_user)

    app = AppRepository.get_by_id(app_id)
    screenshots = app.get("screenshots", [])

    if index < 0 or index >= len(screenshots):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Skrinshot topilmadi"),
        )

    removed_url = screenshots.pop(index)
    _delete_screenshot_file(removed_url)
    AppRepository.update(app_id, {"screenshots": screenshots})

    return success_response({"screenshots": screenshots, "removed": removed_url})
