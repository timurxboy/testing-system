from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base
from core.db.mixins import IDMixin, ReprMixin, TableNameMixin, TimestampMixin

QUESTION_COUNT_CHOICES: tuple[int, ...] = (25, 50, 100)


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

    preferred_question_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    @property
    def is_registered(self) -> bool:
        return bool(self.student_id)

    @property
    def is_setup_complete(self) -> bool:
        return self.is_registered and self.preferred_question_count is not None

    def __str__(self) -> str:
        return self.student_id or f"tg:{self.telegram_id}"
