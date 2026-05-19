from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.testing.models.question import Question
from core.db.base import Base
from core.db.mixins import IDMixin, ReprMixin, TableNameMixin, TimestampMixin


class AnswerOption(Base, IDMixin, TimestampMixin, TableNameMixin, ReprMixin):
    question_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    text: Mapped[str] = mapped_column(
        String(length=512),
        nullable=False,
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    question: Mapped[Question] = relationship(back_populates="options")

    def __str__(self) -> str:
        return self.text[:60]
