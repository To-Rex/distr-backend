from fastapi import APIRouter, Depends, HTTPException, status

from apps.app_store.middleware.auth import get_current_user, require_admin
from apps.app_store.services.user_service import UserService
from apps.app_store.utils.response import success_response, error_response, paginated_response

router = APIRouter(prefix="/admin", tags=["AppStore Admin Users"])


@router.get("/users")
def admin_get_users(
    page: int = 1,
    limit: int = 20,
    role: str = None,
    q: str = None,
    current_user: dict = Depends(require_admin),
):
    users, total = UserService.get_all(q=q, role=role, page=page, limit=limit)
    return paginated_response(users, page, limit, total)


@router.get("/users/{user_id}")
def admin_get_user(user_id: str, current_user: dict = Depends(require_admin)):
    user = UserService.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Foydalanuvchi topilmadi"),
        )
    return success_response(user)


@router.post("/users", status_code=status.HTTP_201_CREATED)
def admin_create_user(
    body: dict,
    current_user: dict = Depends(require_admin),
):
    required = ["username", "email", "password", "displayName", "role"]
    for field in required:
        if field not in body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(f"{field} majburiy maydon"),
            )

    user, err = UserService.create(
        username=body["username"],
        email=body["email"],
        password=body["password"],
        display_name=body["displayName"],
        role=body.get("role", "publisher"),
    )
    if err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response(err),
        )
    return success_response(user)


@router.put("/users/{user_id}")
def admin_update_user(
    user_id: str,
    body: dict,
    current_user: dict = Depends(require_admin),
):
    user = UserService.update(
        user_id,
        displayName=body.get("displayName"),
        email=body.get("email"),
        role=body.get("role"),
        password=body.get("password"),
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("Foydalanuvchi topilmadi"),
        )
    return success_response(user)


@router.delete("/users/{user_id}")
def admin_delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
):
    if user_id == current_user["sub"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response("O'zingizni o'chira olmaysiz"),
        )
    UserService.delete(user_id)
    return success_response(message="Foydalanuvchi muvaffaqiyatli o'chirildi")
