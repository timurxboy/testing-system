from sqladmin import ModelView

from apps.auth.admin.mixins import AdminMixin
from apps.bot.models.tg_admin import TgAdmin


class TgAdminAdmin(AdminMixin, ModelView, model=TgAdmin):
    name = "Bot admin"
    name_plural = "Bot admins"
    category = "Bot"
    icon = "fa-solid fa-user-shield"

    column_list = [
        TgAdmin.id,
        TgAdmin.telegram_id,
        TgAdmin.label,
        TgAdmin.is_active,
        TgAdmin.created_at,
    ]
    column_searchable_list = [TgAdmin.telegram_id, TgAdmin.label]
    column_sortable_list = [TgAdmin.id, TgAdmin.telegram_id, TgAdmin.is_active]

    form_create_rules = ["telegram_id", "label", "is_active"]
    form_edit_rules = ["telegram_id", "label", "is_active"]
