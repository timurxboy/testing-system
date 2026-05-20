from sqladmin import ModelView

from apps.auth.admin.mixins import AdminMixin
from apps.bot.models.bot_user import BotUser


class BotUserAdmin(AdminMixin, ModelView, model=BotUser):
    name = "Foydalanuvchi"
    name_plural = "Foydalanuvchilar"
    category = "Bot"
    icon = "fa-solid fa-user"

    column_list = [
        BotUser.id,
        BotUser.student_id,
        BotUser.telegram_id,
        BotUser.telegram_username,
        BotUser.created_at,
    ]
    column_searchable_list = [
        BotUser.telegram_id,
        BotUser.telegram_username,
        BotUser.student_id,
    ]
    column_sortable_list = [
        BotUser.id,
        BotUser.student_id,
        BotUser.telegram_id,
        BotUser.created_at,
    ]
    column_labels = {
        "id": "ID",
        "student_id": "Shaxsiy ID",
        "telegram_id": "Telegram ID",
        "telegram_username": "Username",
        "created_at": "Yaratilgan",
    }

    can_create = False
    form_edit_rules = ["student_id", "telegram_username"]
