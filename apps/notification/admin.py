from sqladmin import ModelView
from sqlalchemy import inspect
from typing import Any
from starlette.requests import Request
from apps.notification.models import Notification, NotificationUserStatus


class NotificationAdmin(ModelView, model=Notification):
    column_list = [
        Notification.id,
        Notification.title,
        Notification.user_type,
        Notification.company_id,
        Notification.user_1c_id,
        Notification.date,
        Notification.author,
        Notification.created_at
    ]
    column_searchable_list = [
        Notification.title,
        "user_rel.username",
        "company_rel.name",
    ]
    column_filterable_list = [
        Notification.user_type,
        Notification.company_id,
        Notification.user_1c_id,
    ]
    column_default_sort = [(Notification.id, True)]

    name = "Notification"
    icon = "fa-solid fa-bell"


class NotificationUserStatusAdmin(ModelView, model=NotificationUserStatus):
    column_list = [
        NotificationUserStatus.id,
        "notification_rel.title",
        "user_rel.username",
        NotificationUserStatus.is_read,
        NotificationUserStatus.read_at,
        NotificationUserStatus.created_at
    ]
    column_searchable_list = [
        "notification_rel.title",
        "user_rel.username"
    ]
    column_filterable_list = [
        NotificationUserStatus.is_read,
        NotificationUserStatus.user_id
    ]
    column_default_sort = [(NotificationUserStatus.id, True)]

    name = "Notification Status"
    icon = "fa-solid fa-check-double"
