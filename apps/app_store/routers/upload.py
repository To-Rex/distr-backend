from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from apps.app_store.middleware.auth import get_current_user
from apps.app_store.services.upload_service import UploadService
from apps.app_store.utils.response import success_response, error_response

router = APIRouter(prefix="/upload", tags=["AppStore Upload"])


@router.post("/icon")
async def upload_icon(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    content = await file.read()
    if len(content) > 512 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("Fayl hajmi 512KB dan oshmasligi kerak"),
        )
    result = UploadService.upload_icon(content, file.filename)
    return success_response(result)


@router.post("/screenshot")
async def upload_screenshot(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("Fayl hajmi 2MB dan oshmasligi kerak"),
        )
    result = UploadService.upload_screenshot(content, file.filename)
    return success_response(result)


@router.post("/apk")
async def upload_apk(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    content = await file.read()
    if len(content) > 500 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("Fayl hajmi 500MB dan oshmasligi kerak"),
        )
    result = UploadService.upload_apk(content, file.filename)
    return success_response(result)


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    content = await file.read()
    if len(content) > 512 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("Fayl hajmi 512KB dan oshmasligi kerak"),
        )
    result = UploadService.upload_avatar(content, file.filename)
    return success_response(result)
