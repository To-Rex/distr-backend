from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from apps.app_store.middleware.auth import get_current_user
from apps.app_store.models.user import ChangePasswordRequest, LoginRequest
from apps.app_store.services.auth_service import AuthService
from apps.app_store.utils.response import success_response, error_response

router = APIRouter(prefix="/auth", tags=["AppStore Auth"])


@router.post("/login")
def login(body: LoginRequest):
    try:
        result = AuthService.login(body.username, body.password)
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_response(f"Saqlash xizmati bilan ulanib bo'lmadi: {e}"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(f"Ichki xato: {e}"),
        )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("Login yoki parol noto'g'ri"),
        )
    resp = success_response({"token": result["token"], "user": result["user"]})
    response = JSONResponse(content=resp, status_code=200)
    response.set_cookie(
        key="refreshToken",
        value=result["refreshToken"],
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        samesite="lax",
    )
    return response


@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    resp = success_response(message="Muvaffaqiyatli chiqildi")
    response = JSONResponse(content=resp, status_code=200)
    response.delete_cookie(key="refreshToken")
    return response


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    profile = AuthService.get_profile(current_user["sub"])
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Foydalanuvchi topilmadi"),
        )
    return success_response(profile)


@router.put("/profile")
def update_profile(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    return _update_profile_impl(request, current_user)


async def _update_profile_impl(request: Request, current_user: dict):
    form = await request.form()
    display_name = form.get("displayName")
    avatar_file = form.get("avatar")

    avatar_url = None
    if avatar_file and hasattr(avatar_file, "read"):
        from apps.app_store.services.upload_service import UploadService

        content = await avatar_file.read()
        result = UploadService.upload_avatar(content, avatar_file.filename)
        avatar_url = result["url"]

    profile = AuthService.update_profile(
        current_user["sub"],
        display_name=str(display_name) if display_name else None,
        avatar=avatar_url,
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Foydalanuvchi topilmadi"),
        )
    return success_response(profile)


@router.patch("/change-password")
def change_password(
    body: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
):
    ok, msg = AuthService.change_password(
        current_user["sub"], body.currentPassword, body.newPassword
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response(msg),
        )
    return success_response(message=msg)


@router.post("/refresh")
def refresh_token(request: Request):
    refresh_token_str = request.cookies.get("refreshToken")
    if not refresh_token_str:
        body = None
        try:
            import json

            body = json.loads(request.query_params.get("body", "{}"))
        except Exception:
            pass

    result = AuthService.refresh_token(refresh_token_str or "")
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("Refresh token muddati o'tgan. Qayta tizimga kiring"),
        )
    return success_response(result)
