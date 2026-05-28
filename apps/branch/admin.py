from sqladmin import ModelView
from .models import Branch


class BranchAdmin(ModelView, model=Branch):
    icon = "fa-solid fa-code-branch"
    column_list = [Branch.id, Branch.name,
                   Branch.company_id, Branch.created_at]
    column_searchable_list = [Branch.name]
    column_sortable_list = [Branch.id, Branch.name,
                            Branch.company_id, Branch.created_at]
    column_labels = {
        'id': 'ID',
        'name': 'Branch Name',
        'company_id': 'Company ID',
        'created_at': 'Created At',
        'updated_at': 'Updated At',
    }
