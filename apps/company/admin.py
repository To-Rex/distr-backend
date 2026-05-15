
from sqladmin import ModelView
from .models import Company, SecurityKey


class CompanyAdmin(ModelView, model=Company):
    icon = "fas fa-building"
    column_list = [Company.id, Company.name, Company.created_at]
    column_searchable_list = [Company.name]
    # Optionally show SecurityKey in details
    column_details_list = [Company.id, Company.name, Company.inn, Company.base_url,
                           Company.asl_belgi_token, Company.created_at, Company.updated_at,
                           Company.security_key_rel]


class SecurityKeyAdmin(ModelView, model=SecurityKey):
    icon = "fas fa-key"
    column_list = [SecurityKey.id, SecurityKey.key,
                   SecurityKey.company_id, SecurityKey.created_at]
    column_searchable_list = [SecurityKey.key]
    column_sortable_list = [SecurityKey.id,
                            SecurityKey.company_id, SecurityKey.created_at]
    column_labels = {
        'id': 'ID',
        'key': 'Security Key',
        'company_id': 'Company ID',
        'created_at': 'Created At',
        'updated_at': 'Updated At',
    }
