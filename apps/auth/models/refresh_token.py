from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.base import Base
from apps.auth.models.admin_user import AdminUser


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("adminusers.id", ondelete="CASCADE"),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped[AdminUser] = relationship(backref="refresh_tokens")
