from sqladmin import ModelView

from apps.auth.models.admin_user import AdminUser
from apps.auth.admin.mixins import AdminMixin
from apps.auth.utils.password_hash import hash_password


class AdminUserAdmin(AdminMixin, ModelView, model=AdminUser):
    name = "Admin User"
    name_plural = "Admin Users"

    column_list = [
        AdminUser.id,
        AdminUser.username,
        AdminUser.role,
        AdminUser.is_active,
        AdminUser.created_at,
    ]

    column_searchable_list = [
        AdminUser.username,
    ]

    column_sortable_list = [
        AdminUser.id,
        AdminUser.username,
        AdminUser.is_active,
        AdminUser.created_at,
    ]
    column_labels = {"password_hashed": "Password"}

    # ---- Forms ----
    form_create_rules = ["username", "password_hashed", "role", "is_active"]
    form_edit_rules = ["username", "password_hashed", "role", "is_active"]

    async def on_model_change(
        self,
        data: dict,
        model: AdminUser,
        is_created: bool,
        request,
    ) -> None:
        password = data.get("password_hashed")
        if password:
            data["password_hashed"] = hash_password(password)
