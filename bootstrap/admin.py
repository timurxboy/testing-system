from fastapi import FastAPI
from sqladmin import Admin

from apps.auth.admin.admin_user import AdminUserAdmin
from apps.auth.utils.admin_auth import AdminAuthBackend
from apps.bot.admin import BotUserAdmin, TestAttemptAdmin, TgAdminAdmin
from apps.testing.admin import AnswerOptionAdmin, QuestionAdmin, SubjectAdmin
from core.db import engine
from core.settings import core_settings


def setup_admin(app: FastAPI) -> None:
    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=AdminAuthBackend(secret_key=core_settings.SECRET_KEY),
    )

    admin.add_view(AdminUserAdmin)

    admin.add_view(SubjectAdmin)
    admin.add_view(QuestionAdmin)
    admin.add_view(AnswerOptionAdmin)

    admin.add_view(BotUserAdmin)
    admin.add_view(TgAdminAdmin)
    admin.add_view(TestAttemptAdmin)
