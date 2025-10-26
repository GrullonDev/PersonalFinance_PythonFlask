from datetime import date
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Date, Enum as SAEnum, ForeignKey, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.models.category import TipoMovimiento

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_profile_fecha", "profile_id", "fecha"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    tipo: Mapped[TipoMovimiento] = mapped_column(SAEnum(TipoMovimiento, name="tipo_movimiento"), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    es_recurrente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    profile: Mapped["Profile"] = relationship(back_populates="transactions")
    categoria: Mapped["Category"] = relationship(back_populates="transactions")
