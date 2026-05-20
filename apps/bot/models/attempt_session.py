from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.bot.models.bot_user import BotUser
from apps.testing.models.subject import Subject
from core.db.base import Base
from core.db.mixins import IDMixin, ReprMixin, TableNameMixin, TimestampMixin


class AttemptSessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABORTED = "aborted"


class AttemptSession(Base, IDMixin, TimestampMixin, TableNameMixin, ReprMixin):
    bot_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("botusers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subject_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[AttemptSessionStatus] = mapped_column(
        String(length=20),
        nullable=False,
        default=AttemptSessionStatus.ACTIVE,
        index=True,
    )

    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    round_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        index=True,
    )

    # Полный упорядоченный список вопросов, выданных в этой попытке.
    question_ids: Mapped[list[int]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    current_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    correct_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    bot_user: Mapped[BotUser] = relationship()
    subject: Mapped[Subject] = relationship()

    @property
    def total_questions(self) -> int:
        return len(self.question_ids)
