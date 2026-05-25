from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from apps.app_store.services.app_service import AppService
from apps.app_store.services.version_service import VersionService
from apps.app_store.services.minio_storage import get_object
from apps.app_store.utils.response import success_response, error_response, paginated_response

router = APIRouter(prefix="", tags=["AppStore Apps Public"])


@router.get("/apps/featured")
def get_featured(limit: int = 3):
    apps = AppService.get_featured(limit)
    return success_response(apps)


@router.get("/apps/recently-updated")
def get_recently_updated(limit: int = 4):
    apps = AppService.get_recently_updated(limit)
    return success_response(apps)


@router.get("/apps/newest")
def get_newest(limit: int = 4):
    apps = AppService.get_newest(limit)
    return success_response(apps)


@router.get("/apps/search-suggestions")
def search_suggestions(q: str, limit: int = 5):
    if len(q) < 2:
        return success_response([])
    apps = AppService.get_search_suggestions(q, limit)
    return success_response(apps)


@router.get("/apps/{app_id}/versions")
def get_versions(app_id: str, sort: str = "newest", page: int = 1, limit: int = 20):
    result = VersionService.get_versions(app_id, sort=sort, page=page, limit=limit)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Ilova topilmadi"),
        )
    versions, total = result
    return paginated_response(versions, page, limit, total)


@router.get("/apps/{app_id}/versions/{version}")
def get_single_version(app_id: str, version: str):
    result = VersionService.get_single_version(app_id, version)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Versiya topilmadi"),
        )
    return success_response(result)


@router.get("/apps/{app_id}/versions/{version}/download")
def download_version(app_id: str, version: str):
    v = VersionService.download_version(app_id, version)
    if not v:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Versiya topilmadi"),
        )

    file_path = v.get("filePath", "")
    if file_path:
        data = get_object(file_path)
        if data:
            app = AppService.get_by_id(app_id)
            app_name = app["name"] if app else "App"
            download_filename = f"{app_name} v{version}.apk"
            data.seek(0)
            return StreamingResponse(
                data,
                media_type="application/vnd.android.package-archive",
                headers={"Content-Disposition": f'attachment; filename="{download_filename}"'},
            )

    from apps.app_store.config import BASE_URL

    download_url = f"{BASE_URL}/apps/{app_id}/versions/{version}/download"
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=download_url)


@router.get("/apps/{app_id}/screenshots")
def get_screenshots(app_id: str):
    result = AppService.get_screenshots(app_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Ilova topilmadi"),
        )
    return success_response(result)


@router.get("/apps")
def get_apps(
    q: str = None,
    category: str = None,
    sort: str = "updated",
    page: int = 1,
    limit: int = 20,
    published: bool = True,
):
    apps, total = AppService.get_public_list(
        q=q, category=category, sort=sort, page=page, limit=limit, published=published
    )
    return paginated_response(apps, page, limit, total)


@router.get("/apps/{app_id}")
def get_app(app_id: str):
    app = AppService.get_by_id(app_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Ilova topilmadi"),
        )
    return success_response(app)
