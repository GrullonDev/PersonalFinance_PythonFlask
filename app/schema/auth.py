from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    nombres: str = Field(min_length=1, max_length=150)
    apellidos: str = Field(min_length=1, max_length=150)
    fecha_nacimiento: date | None = None
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    firebase_uid: str | None = Field(default=None, min_length=1, max_length=128)
    email: EmailStr
    email_confirmacion: EmailStr
    password: str = Field(min_length=8, max_length=128)
    password_confirmacion: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_confirmations(self) -> "RegisterRequest":
        if self.email.lower() != self.email_confirmacion.lower():
            raise ValueError("El email y su confirmación deben coincidir")
        if self.password != self.password_confirmacion:
            raise ValueError("La contraseña y su confirmación deben coincidir")
        return self

    def normalized_email(self) -> str:
        return self.email.lower()

    def normalized_username(self) -> str:
        return self.username.lower()

    def normalized_firebase_uid(self) -> str | None:
        if self.firebase_uid is None:
            return None
        return self.firebase_uid.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

    def normalized_email(self) -> str:
        return self.email.strip().lower()


class PasswordRecoveryRequest(BaseModel):
    identificador: str = Field(min_length=1)


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=1)
    password: str = Field(min_length=8, max_length=128)
    password_confirmacion: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_password_confirmation(self) -> "PasswordResetConfirmRequest":
        if self.password != self.password_confirmacion:
            raise ValueError("La contraseña y su confirmación deben coincidir")
        return self


class LocalUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    firebase_uid: str
    email: EmailStr
    username: str | None
    nombres: str | None
    apellidos: str | None
    nombre_completo: str
    fecha_nacimiento: date | None
    fecha_creacion: datetime
    fecha_actualizacion: datetime


class LocalLoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: LocalUserRead


class MessageResponse(BaseModel):
    detail: str
