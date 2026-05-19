from fastapi import Request
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
import jwt

from core.db import SessionLocal
from apps.auth.models.admin_user import AdminUser
from apps.auth.domain.roles import Role


class AdminAuthBackend(AuthenticationBackend):
    def __init__(self, *, secret_key: str):
        super().__init__(secret_key=secret_key)
        self.secret_key = secret_key

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not username or not password:
            return False

        async with SessionLocal() as session:
            result = await session.execute(
                select(AdminUser).where(AdminUser.username == username)
            )
            user = result.scalar_one_or_none()

        if not user or not user.is_active:
            return False

        if not user.verify_password(password):
            return False

        if user.role not in (Role.ADMIN, Role.STAFF):
            return False

        token = jwt.encode(
            {"sub": str(user.id), "role": user.role},
            self.secret_key,
            algorithm="HS256",
        )

        request.session.update({"token": token})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False

        try:
            jwt.decode(token, self.secret_key, algorithms=["HS256"])
        except jwt.PyJWTError:
            return False

        return True
