from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

class GoalBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    monto_objetivo: Decimal = Field(gt=0)
    monto_actual: Decimal = Field(ge=0, default=0)
    fecha_limite: date
    icono: str | None = Field(default=None, max_length=64)

class GoalCreate(GoalBase):
    pass

class GoalUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=150)
    monto_objetivo: Decimal | None = Field(default=None, gt=0)
    monto_actual: Decimal | None = Field(default=None, ge=0)
    fecha_limite: date | None = None
    icono: str | None = Field(default=None, max_length=64)

class GoalRead(GoalBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)
