from __future__ import annotations

from datetime import date
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    monto_objetivo: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    monto_actual: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    fecha_limite: Mapped[date] = mapped_column(Date, nullable=False)
    icono: Mapped[str | None] = mapped_column(String(64), nullable=True)

    profile: Mapped["Profile"] = relationship(back_populates="goals")
