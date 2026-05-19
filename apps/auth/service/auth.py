from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from apps.auth.domain.roles import Role
from apps.auth.models.admin_user import AdminUser
from apps.auth.models.refresh_token import RefreshToken
from apps.auth.utils.jwt import create_access_token, create_refresh_token
from core.settings import core_settings


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _issue_tokens(self, user: AdminUser) -> tuple[str, str]:
        access = create_access_token(
            subject=user.id,
            role=user.role,
        )
        refresh_value = create_refresh_token()

        refresh = RefreshToken(
            token=refresh_value,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(
                days=core_settings.REFRESH_TOKEN_EXPIRE_DAYS,
            ),
        )

        self.session.add(refresh)
        await self.session.flush()

        return access, refresh_value

    async def _get_user_by_username(self, username: str) -> AdminUser | None:
        result = await self.session.execute(
            select(AdminUser).where(AdminUser.username == username)
        )
        return result.scalar_one_or_none()

    async def create_admin(
        self,
        *,
        username: str,
        password: str,
        role: Role = Role.STAFF,
    ) -> AdminUser:
        existing = await self._get_user_by_username(username)
        if existing:
            raise ValueError(f"User '{username}' already exists")

        user = AdminUser(
            username=username,
            role=role,
        )
        user.password = password

        self.session.add(user)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return user

    async def login(self, *, username: str, password: str) -> tuple[str, str]:
        user = await self._get_user_by_username(username)

        if not user or not user.verify_password(password):
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("User account is deactivated")

        access, refresh_value = await self._issue_tokens(user)

        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return access, refresh_value

    async def refresh(self, refresh_token: str) -> str:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        token = result.scalar_one_or_none()

        if not token or token.expires_at < datetime.now(timezone.utc):
            raise ValueError("Invalid or expired refresh token")

        user = await self.session.get(AdminUser, token.user_id)

        if not user or not user.is_active:
            raise ValueError("User not found or deactivated")

        return create_access_token(
            subject=user.id,
            role=user.role,
        )

    async def logout(self, refresh_token: str) -> None:
        await self.session.execute(
            delete(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def register(self, *, username: str, password: str) -> tuple[str, str]:
        existing = await self._get_user_by_username(username)
        if existing:
            raise ValueError("User already exists")

        user = AdminUser(
            username=username,
            role=Role.USER,
        )
        user.password = password

        self.session.add(user)
        access, refresh_value = await self._issue_tokens(user)

        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return access, refresh_value

    async def cleanup_expired_tokens(self) -> int:
        result = await self.session.execute(
            delete(RefreshToken).where(
                RefreshToken.expires_at < datetime.now(timezone.utc)
            )
        )
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return result.rowcount
