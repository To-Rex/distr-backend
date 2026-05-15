from sqladmin import ModelView
from .models import WorkingSession


class WorkingSessionAdmin(ModelView, model=WorkingSession):
    column_list = [
        WorkingSession.id,
        WorkingSession.app,
        WorkingSession.session,
        WorkingSession.device_name,
        WorkingSession.user_rel,
        WorkingSession.is_testing,
        WorkingSession.created_at,
    ]
    column_searchable_list = [WorkingSession.device_name]
    column_sortable_list = [WorkingSession.user_rel]
    column_default_sort = [(WorkingSession.id, True)]
    name = "Working Session"
    icon = "fa-solid fa-clock"
