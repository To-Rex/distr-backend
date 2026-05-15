from fastapi import APIRouter, Depends, HTTPException, Request, status

from apps.app_store.middleware.auth import get_current_user
from apps.app_store.repositories.app_repository import AppRepository
from apps.app_store.services.version_service import VersionService
from apps.app_store.services.upload_service import UploadService
from apps.app_store.utils.response import success_response, error_response

router = APIRouter(prefix="/admin", tags=["AppStore Admin Versions"])


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


@router.post("/apps/{app_id}/versions", status_code=status.HTTP_201_CREATED)
async def admin_create_version(
    app_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    _check_app_access(app_id, current_user)

    form = await request.form()
    version = form.get("version")
    if not version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("Versiya raqami majburiy"),
        )

    file = form.get("file")
    if not file or not hasattr(file, "read"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("APK fayl majburiy"),
        )

    content = await file.read()
    upload_result = UploadService.upload_apk(content, file.filename)

    min_android = str(form.get("minAndroid", "8.0"))
    changelog = str(form.get("changelog", ""))

    result = VersionService.create_version(
        app_id=app_id,
        version=str(version),
        file_size=upload_result["fileSize"],
        min_android=min_android,
        changelog=changelog,
        file_path=upload_result.get("filePath", ""),
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response("Bu versiya allaqachon mavjud yoki ilova topilmadi"),
        )
    return success_response(result)


@router.put("/apps/{app_id}/versions/{version}")
async def admin_update_version(
    app_id: str,
    version: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    _check_app_access(app_id, current_user)

    form = await request.form()
    changelog = form.get("changelog")
    min_android = form.get("minAndroid")
    file = form.get("file")

    file_size = None
    file_path = None
    if file and hasattr(file, "read"):
        content = await file.read()
        upload_result = UploadService.upload_apk(content, file.filename)
        file_size = upload_result["fileSize"]
        file_path = upload_result.get("filePath", "")

    result = VersionService.update_version(
        app_id=app_id,
        version=version,
        changelog=str(changelog) if changelog else None,
        min_android=str(min_android) if min_android else None,
        file_size=file_size,
        file_path=file_path,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Versiya topilmadi"),
        )
    return success_response(result)


@router.delete("/apps/{app_id}/versions/{version}")
def admin_delete_version(
    app_id: str,
    version: str,
    current_user: dict = Depends(get_current_user),
):
    _check_app_access(app_id, current_user)
    deleted = VersionService.delete_version(app_id, version)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Versiya topilmadi"),
        )
    return success_response(message="Versiya muvaffaqiyatli o'chirildi")
