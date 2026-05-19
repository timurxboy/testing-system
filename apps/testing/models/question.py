from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.testing.models.subject import Subject
from core.db.base import Base
from core.db.mixins import IDMixin, ReprMixin, TableNameMixin, TimestampMixin


class Question(Base, IDMixin, TimestampMixin, TableNameMixin, ReprMixin):
    subject_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    text: Mapped[str] = mapped_column(
        String(length=1024),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        index=True,
    )

    subject: Mapped[Subject] = relationship(back_populates="questions")

    options: Mapped[list["AnswerOption"]] = relationship(  # noqa: F821
        back_populates="question",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AnswerOption.id",
    )

    def __str__(self) -> str:
        return f"#{self.id} {self.text[:60]}"
