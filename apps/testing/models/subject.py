from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.base import Base
from core.db.mixins import IDMixin, ReprMixin, TableNameMixin, TimestampMixin


class Subject(Base, IDMixin, TimestampMixin, TableNameMixin, ReprMixin):
    name: Mapped[str] = mapped_column(
        String(length=120),
        unique=True,
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        index=True,
    )

    questions: Mapped[list["Question"]] = relationship(  # noqa: F821
        back_populates="subject",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __str__(self) -> str:
        return self.name
