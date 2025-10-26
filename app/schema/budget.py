from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

class BudgetBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    monto_total: Decimal = Field(gt=0)
    fecha_inicio: date
    fecha_fin: date

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=150)
    monto_total: Decimal | None = Field(default=None, gt=0)
    fecha_inicio: date | None = None
    fecha_fin: date | None = None

class BudgetRead(BudgetBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)
