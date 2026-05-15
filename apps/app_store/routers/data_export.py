import io
import shutil
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status

from apps.app_store.config import DATA_DIR, EXPORTS_DIR, UPLOADS_DIR
from apps.app_store.middleware.auth import require_admin
from apps.app_store.utils.response import success_response, error_response

router = APIRouter(prefix="/admin", tags=["AppStore Admin Data Export"])

EXPORT_FILENAME = "data_export.zip"

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

    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(DATA_DIR.rglob("*")):
            if file_path.is_file():
                rel = file_path.relative_to(DATA_DIR)
                if rel.parts[0] in EXCLUDED_DIRS:
                    continue
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

    names = zf.namelist()

    tmp_dir = tempfile.mkdtemp()
    try:
        zf.extractall(tmp_dir)
        zf.close()

        extracted = Path(tmp_dir)

        if not (extracted / "apps.json").exists() and not any(
            (extracted / p).exists() for p in names if "/" in p
        ):
            pass

        for item in DATA_DIR.iterdir():
            if item.name == "exports" or item.name in KEEP_FILES:
                continue
            if item.is_dir():
                shutil.rmtree(str(item), ignore_errors=True)
            else:
                item.unlink(missing_ok=True)

        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

        for member in names:
            if member.endswith("/"):
                continue
            member_path = extracted / member
            if not member_path.exists():
                continue
            rel = Path(member)
            if rel.parts[0] in EXCLUDED_DIRS:
                continue
            target = DATA_DIR / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(member_path), str(target))
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
    for item in DATA_DIR.iterdir():
        if item.name == "exports" or item.name in KEEP_FILES:
            continue
        if item.is_dir():
            shutil.rmtree(str(item), ignore_errors=True)
        else:
            item.unlink(missing_ok=True)

    for d in [UPLOADS_DIR, EXPORTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

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
