from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base
from core.db.mixins import IDMixin, ReprMixin, TableNameMixin, TimestampMixin


class TgAdmin(Base, IDMixin, TimestampMixin, TableNameMixin, ReprMixin):
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
    )

    label: Mapped[str | None] = mapped_column(
        String(length=120),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        index=True,
    )

    def __str__(self) -> str:
        return f"{self.label or '-'} (tg={self.telegram_id})"
