from sqladmin import ModelView

from apps.auth.admin.mixins import AdminMixin
from apps.bot.models.bot_user import BotUser


class BotUserAdmin(AdminMixin, ModelView, model=BotUser):
    name = "Bot user"
    name_plural = "Bot users"
    category = "Bot"
    icon = "fa-solid fa-user"

    column_list = [
        BotUser.id,
        BotUser.telegram_id,
        BotUser.telegram_username,
        BotUser.first_name,
        BotUser.last_name,
        BotUser.created_at,
    ]
    column_searchable_list = [
        BotUser.telegram_id,
        BotUser.telegram_username,
        BotUser.first_name,
        BotUser.last_name,
    ]
    column_sortable_list = [BotUser.id, BotUser.telegram_id, BotUser.created_at]

    can_create = False
    form_edit_rules = ["first_name", "last_name", "telegram_username"]
