from datetime import date
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        # Un nombre de presupuesto por rango (opcional, ajusta a tu lógica)
        UniqueConstraint("profile_id", "nombre", "fecha_inicio", "fecha_fin", name="uq_budget_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    monto_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)

    profile: Mapped["Profile"] = relationship(back_populates="budgets")
