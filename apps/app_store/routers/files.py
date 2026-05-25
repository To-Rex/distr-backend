from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from apps.app_store.services.minio_storage import get_object

router = APIRouter(tags=["AppStore Files"])

CONTENT_TYPES = {
    ".apk": "application/vnd.android.package-archive",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".zip": "application/zip",
}


@router.get("/uploads/{category}/{filename}")
def serve_upload(category: str, filename: str):
    object_key = f"{category}/{filename}"
    data = get_object(object_key)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fayl topilmadi",
        )
    ext = Path(filename).suffix.lower()
    media_type = CONTENT_TYPES.get(ext, "application/octet-stream")
    data.seek(0)
    return StreamingResponse(data, media_type=media_type)
