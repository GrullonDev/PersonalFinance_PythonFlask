from enum import Enum
from sqlalchemy import String, Integer, Enum as SAEnum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class TipoMovimiento(str, Enum):
    ingreso = "ingreso"
    gasto = "gasto"

class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        # Evita duplicados de nombre por usuario y tipo
        UniqueConstraint("profile_id", "nombre", "tipo", name="uq_category_profile_nombre_tipo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[TipoMovimiento] = mapped_column(SAEnum(TipoMovimiento, name="tipo_movimiento"), nullable=False)

    profile: Mapped["Profile"] = relationship(back_populates="categories")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="categoria")
