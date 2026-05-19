from datetime import datetime

from sqlalchemy import DateTime, BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column, declared_attr


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class IDMixin:
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        index=True,
    )


class TableNameMixin:
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"


class ReprMixin:
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', None)})>"
