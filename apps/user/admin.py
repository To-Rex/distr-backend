from typing import Any

from sqladmin import ModelView
from sqlalchemy import inspect
from starlette.requests import Request

from apps.user.models import User
from config.security import get_password_hash


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id, User.username, User.user_type, User.user_status, User.manager,
        User.company_rel, User.user_1c_id, User.user_1c_login,        User.created_at
    ]
    column_searchable_list = [User.username, "company_rel.name"]
    column_default_sort = [(User.id, True)]
    column_export_list = [
        column for column in inspect(User).mapper.column_attrs]

    icon = "fa-solid fa-users"

    async def on_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        try:
            if "password" in data:
                data["password"] = get_password_hash(data["password"])

            print(f"DEBUG: Processing data: {data}")
        except Exception as e:
            print(f"ERROR in on_model_change: {e}")
            raise e
