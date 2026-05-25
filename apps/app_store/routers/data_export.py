import io
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status

from apps.app_store.config import EXPORTS_DIR, USERS_JSON, APPS_JSON, VERSIONS_JSON, CATEGORIES_JSON
from apps.app_store.middleware.auth import require_admin
from apps.app_store.services.minio_storage import (
    get_json,
    put_json,
    get_object,
    upload_bytes,
    download_to_dir,
    upload_dir,
    delete_all,
    delete_file,
)
from apps.app_store.utils.response import success_response, error_response

router = APIRouter(prefix="/admin", tags=["AppStore Admin Data Export"])

EXPORT_FILENAME = "data_export.zip"

JSON_KEYS = [USERS_JSON, APPS_JSON, VERSIONS_JSON, CATEGORIES_JSON]

EXCLUDED_DIRS = {"exports"}
KEEP_FILES = {"categories.json"}


@router.get(
    "/data/export",
    summary="Ma'lumotlarni eksport qilish",
    description="Butun data jildini ZIP arxiv sifatida yaratish va yuklab olish URL qaytarish. Faqat admin uchun. Har yangi export avvalgisini replace qiladi.",
)
def export_data(current_user: dict = Depends(require_admin)):
    zip_path = EXPORTS_DIR / EXPORT_FILENAME

    if zip_path.exists():
        zip_path.unlink()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        for object_key in sorted(JSON_KEYS):
            data = get_json(object_key)
            content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            dest = tmp / object_key
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)

        uploads_tmp = tmp / "uploads"
        uploads_tmp.mkdir(parents=True, exist_ok=True)
        download_to_dir("", uploads_tmp)

        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in sorted(tmp.rglob("*")):
                if file_path.is_file():
                    rel = file_path.relative_to(tmp)
                    zf.write(str(file_path), str(rel))

    return success_response(
        {
            "message": "Ma'lumotlar muvaffaqiyatli eksport qilindi",
            "download_url": f"/appstore/exports/{EXPORT_FILENAME}",
            "filename": EXPORT_FILENAME,
        }
    )


@router.post(
    "/data/import",
    summary="Ma'lumotlarni import qilish",
    description="ZIP arxivni yuklab, joriy ma'lumotlarni almashtirish. Faqat admin uchun. Eksport qilingan ZIP faylni qayta import qilish mumkin.",
)
async def import_data(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_admin),
):
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("Faqat ZIP fayl yuklash mumkin"),
        )

    content = await file.read()

    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response("Noto'g'ri ZIP fayl"),
        )

    tmp_dir = tempfile.mkdtemp()
    try:
        zf.extractall(tmp_dir)
        zf.close()

        extracted = Path(tmp_dir)

        known_keys = {key.split("/")[-1]: key for key in JSON_KEYS}
        for filename, object_key in known_keys.items():
            file_path = extracted / "data" / filename
            if not file_path.exists():
                file_path = extracted / filename
            if file_path.exists():
                data = json.loads(file_path.read_bytes())
                if isinstance(data, list):
                    put_json(object_key, data)

        uploads_extracted = extracted / "uploads"
        if uploads_extracted.exists() and uploads_extracted.is_dir():
            delete_all()
            upload_dir(uploads_extracted, "")

        any_upload_file = any(
            not (name.endswith("/") or Path(name).parts[0] == "data")
            for name in zf.namelist()
        )
        if any_upload_file and (
            not (uploads_extracted.exists() and uploads_extracted.is_dir())
        ):
            members = zf.namelist()
            for member in members:
                if member.endswith("/"):
                    continue
                parts = Path(member).parts
                if parts[0] == "data":
                    continue
                if parts[0] == "uploads":
                    continue
                member_path = extracted / member
                if member_path.exists():
                    delete_file(str(Path(member)))
                    content = member_path.read_bytes()
                    ext = Path(member).suffix.lower()
                    content_type = {
                        ".apk": "application/vnd.android.package-archive",
                        ".png": "image/png",
                        ".jpg": "image/jpeg",
                        ".jpeg": "image/jpeg",
                        ".webp": "image/webp",
                        ".zip": "application/zip",
                    }.get(ext, "application/octet-stream")
                    upload_bytes(str(Path(member)), content, content_type)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return success_response(
        message="Ma'lumotlar muvaffaqiyatli import qilindi",
    )


@router.post(
    "/data/clear",
    summary="Ma'lumotlarni tozalash",
    description="AppStore'ga tegishli barcha ma'lumotlarni o'chirib, dastlabki holatga qaytarish. Faqat admin uchun. Admin foydalanuvchi qayta tiklanadi (admin/admin123).",
)
def clear_data(current_user: dict = Depends(require_admin)):
    delete_all()

    from apps.app_store.repositories.user_repository import UserRepository
    from apps.app_store.services.auth_service import AuthService
    from datetime import date

    admin_user = {
        "id": "user-admin-001",
        "username": "admin",
        "email": "admin@torex.uz",
        "password": AuthService.hash_password("admin123"),
        "role": "admin",
        "displayName": "Admin",
        "avatar": None,
        "createdAt": date.today().isoformat(),
    }
    UserRepository.create(admin_user)

    return success_response(
        message="Ma'lumotlar muvaffaqiyatli tozalandi. Dastlabki holatga qaytarildi.",
    )
