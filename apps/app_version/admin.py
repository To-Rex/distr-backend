from sqladmin import ModelView

from config.settings import settings
from .models import App, Version


class AppAdmin(ModelView, model=App):
    column_list = [App.id, App.name, App.created_at]
    column_searchable_list = [App.name]
    icon = "fa-solid fa-mobile"


class VersionAdmin(ModelView, model=Version):
    column_list = [
        Version.id,
        "app_rel.name",
        Version.version,
        Version.build_number,
        Version.force_update,
        Version.update_url,
        Version.title,
        Version.created_at,
    ]

    # Sort by ID descending (True indicates descending)
    column_default_sort = [(Version.id, True)]

    icon = "fa-solid fa-code-branch"

    async def on_model_change(self, data, model, is_created, request):
        """Runs before saving to the database."""
        url = data.get("update_url")

        if url and url.startswith("/static/") and not url.startswith("http"):
            full_url = f"{settings.BASE_URL.rstrip('/')}/{url.lstrip('/')}"
            model.update_url = full_url
            data["update_url"] = full_url

        return await super().on_model_change(data, model, is_created, request)
