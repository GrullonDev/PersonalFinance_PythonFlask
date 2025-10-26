from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class ProfileBase(BaseModel):
    firebase_uid: str = Field(min_length=1, max_length=128)
    email: EmailStr
    nombre_completo: str = Field(min_length=1, max_length=255)

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(BaseModel):
    nombre_completo: str | None = Field(default=None, min_length=1, max_length=255)

class ProfileRead(ProfileBase):
    id: int
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)
