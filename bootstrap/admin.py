from fastapi import FastAPI
from sqladmin import Admin

from core.db import engine
from core.settings import core_settings

from apps.auth.utils.admin_auth import AdminAuthBackend
from apps.auth.admin.admin_user import AdminUserAdmin


def setup_admin(app: FastAPI) -> None:
    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=AdminAuthBackend(secret_key=core_settings.SECRET_KEY),
    )

    admin.add_view(view=AdminUserAdmin)
