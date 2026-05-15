
from sqladmin import ModelView

from apps import location
from .models import Location


class LocationAdmin(ModelView, model=Location):
    column_list = [
        Location.id, Location.user_rel,
        Location.device_name, Location.latitude,
        Location.longitude, Location.created_at
    ]
    column_searchable_list = [Location.latitude]

    column_sortable_list = [Location.user_rel,]

    column_default_sort = [(Location.id, True)]

    name = "Location"
    icon = "fa-solid fa-location-dot"
