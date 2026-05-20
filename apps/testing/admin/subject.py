from sqladmin import ModelView

from apps.auth.admin.mixins import AdminMixin
from apps.testing.models.subject import Subject


class SubjectAdmin(AdminMixin, ModelView, model=Subject):
    name = "Fan"
    name_plural = "Fanlar"
    category = "Testlar"
    icon = "fa-solid fa-book"

    column_list = [
        Subject.id,
        Subject.name,
        Subject.is_active,
        Subject.created_at,
    ]
    column_searchable_list = [Subject.name]
    column_sortable_list = [Subject.id, Subject.name, Subject.is_active, Subject.created_at]
    column_labels = {
        "id": "ID",
        "name": "Nomi",
        "is_active": "Faol",
        "created_at": "Yaratilgan",
    }

    form_create_rules = ["name", "is_active"]
    form_edit_rules = ["name", "is_active"]
