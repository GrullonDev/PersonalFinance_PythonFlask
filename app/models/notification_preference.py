from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class NotificationPreference(Base, TimestampMixin):
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    push_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    marketing_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    profile: Mapped["Profile"] = relationship(back_populates="notification_preference")

