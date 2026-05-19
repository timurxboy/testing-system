from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base
from core.db.mixins import IDMixin, ReprMixin, TableNameMixin, TimestampMixin


class BotUser(Base, IDMixin, TimestampMixin, TableNameMixin, ReprMixin):
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
    )

    telegram_username: Mapped[str | None] = mapped_column(
        String(length=64),
        nullable=True,
    )

    first_name: Mapped[str | None] = mapped_column(
        String(length=120),
        nullable=True,
    )

    last_name: Mapped[str | None] = mapped_column(
        String(length=120),
        nullable=True,
    )

    @property
    def is_registered(self) -> bool:
        return bool(self.first_name) and bool(self.last_name)

    @property
    def full_name(self) -> str:
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    def __str__(self) -> str:
        return f"{self.full_name or '-'} (tg={self.telegram_id})"
