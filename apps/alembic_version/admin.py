from sqladmin import ModelView
from apps.alembic_version.models import AlembicVersion


class AlembicVersionAdmin(ModelView, model=AlembicVersion):
    column_list = [
        AlembicVersion.version_num
    ]
    column_searchable_list = [
        AlembicVersion.version_num
    ]
    column_filterable_list = [
        AlembicVersion.version_num
    ]
    

    name = "Alembic Version"
    icon = "fa-solid fa-tag"