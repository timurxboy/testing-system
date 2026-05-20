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

    student_id: Mapped[str | None] = mapped_column(
        String(length=64),
        unique=True,
        nullable=True,
        index=True,
    )

    @property
    def is_registered(self) -> bool:
        return bool(self.student_id)

    def __str__(self) -> str:
        return self.student_id or f"tg:{self.telegram_id}"
