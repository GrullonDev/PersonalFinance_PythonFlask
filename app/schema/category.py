from pydantic import BaseModel, Field, ConfigDict
from app.models.category import TipoMovimiento

class CategoryBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    tipo: TipoMovimiento

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=100)
    tipo: TipoMovimiento | None = None

class CategoryRead(CategoryBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)
