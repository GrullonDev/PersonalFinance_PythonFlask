from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from app.models.category import TipoMovimiento

class TransactionBase(BaseModel):
    tipo: TipoMovimiento
    monto: Decimal = Field(gt=0)
    descripcion: str | None = Field(default=None, max_length=500)
    fecha: date
    categoria_id: int
    es_recurrente: bool = False

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    tipo: TipoMovimiento | None = None
    monto: Decimal | None = Field(default=None, gt=0)
    descripcion: str | None = Field(default=None, max_length=500)
    fecha: date | None = None
    categoria_id: int | None = None
    es_recurrente: bool | None = None

class TransactionRead(TransactionBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)
