from sqlalchemy import BigInteger, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.bot.models.bot_user import BotUser
from apps.testing.models.answer_option import AnswerOption
from apps.testing.models.question import Question
from apps.testing.models.subject import Subject
from core.db.base import Base
from core.db.mixins import IDMixin, ReprMixin, TableNameMixin, TimestampMixin


class TestAttempt(Base, IDMixin, TimestampMixin, TableNameMixin, ReprMixin):
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

    question_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    selected_option_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("answeroptions.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        index=True,
    )

    bot_user: Mapped[BotUser] = relationship()
    subject: Mapped[Subject] = relationship()
    question: Mapped[Question] = relationship()
    selected_option: Mapped[AnswerOption | None] = relationship()
