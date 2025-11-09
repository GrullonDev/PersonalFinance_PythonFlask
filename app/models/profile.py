from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Profile(Base, TimestampMixin):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    nombres: Mapped[str | None] = mapped_column(String(150), nullable=True)
    apellidos: Mapped[str | None] = mapped_column(String(150), nullable=True)
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date(), nullable=True)
    username: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)

    # Relaciones
    categories: Mapped[list["Category"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    goals: Mapped[list["Goal"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    local_credential: Mapped["LocalCredential | None"] = relationship(
        back_populates="profile", cascade="all, delete-orphan", uselist=False
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    notification_preference: Mapped["NotificationPreference | None"] = relationship(
        back_populates="profile", cascade="all, delete-orphan", uselist=False
    )
