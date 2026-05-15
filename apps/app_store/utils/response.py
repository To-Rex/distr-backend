from typing import Any, Optional


def success_response(data: Any = None, message: Optional[str] = None) -> dict:
    resp: dict[str, Any] = {"success": True}
    if data is not None:
        resp["data"] = data
    if message is not None:
        resp["message"] = message
    return resp


def error_response(error: str) -> dict:
    return {"success": False, "error": error}


def paginated_response(data: list, page: int, limit: int, total: int) -> dict:
    total_pages = max(1, -(-total // limit))
    return {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": total_pages,
        },
    }
