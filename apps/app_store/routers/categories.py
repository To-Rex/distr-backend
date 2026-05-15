from fastapi import APIRouter

from apps.app_store.services.category_service import CategoryService
from apps.app_store.utils.response import success_response

router = APIRouter(prefix="", tags=["AppStore Categories"])


@router.get("/categories")
def get_categories():
    categories = CategoryService.get_all()
    return success_response(categories)
