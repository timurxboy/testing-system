from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property

from apps.auth.domain.roles import Role
from core.db.base import Base
from core.db.mixins import (
    IDMixin,
    TimestampMixin,
    TableNameMixin,
    ReprMixin,
)

from apps.auth.utils.password_hash import (
    hash_password,
    check_password_hash,
)


class AdminUser(
    Base,
    IDMixin,
    TimestampMixin,
    TableNameMixin,
    ReprMixin,
):
    username: Mapped[str] = mapped_column(
        String(length=50),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hashed: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )

    role: Mapped[Role] = mapped_column(
        String(20),
        nullable=False,
        default=Role.ADMIN,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        index=True,
    )

    # ---- password API ----

    @hybrid_property
    def password(self) -> str:
        raise AttributeError("Password is write-only")

    @password.setter
    def password(self, plaintext_password: str) -> None:
        self.password_hashed = hash_password(password=plaintext_password)

    def verify_password(self, password: str) -> bool:
        return check_password_hash(plain_password=password, hashed_password=self.password_hashed)

    def __str__(self) -> str:
        return f"id={self.id} username={self.username}"
