from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.local_credential import LocalCredential
from app.models.password_reset_token import PasswordResetToken
from app.models.profile import Profile
from app.models.user import User
from app.schema.auth import (
    LocalUserRead,
    LoginRequest,
    MessageResponse,
    PasswordRecoveryRequest,
    PasswordResetConfirmRequest,
    RegisterRequest,
)
from app.services.email import send_password_reset_email
from app.services.security import hash_password, verify_password


router = APIRouter(tags=["auth"])


def _normalize(text: str) -> str:
    return text.strip().lower()


@router.post("/register", response_model=LocalUserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)) -> LocalUserRead:
    email = payload.normalized_email()
    username = payload.normalized_username()

    email_exists_stmt = select(Profile.id).where(func.lower(Profile.email) == email)
    if db.execute(email_exists_stmt).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email",
        )

    username_exists_stmt = select(Profile.id).where(func.lower(Profile.username) == username)
    if db.execute(username_exists_stmt).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese nombre de usuario",
        )

    firebase_uid = f"local-{uuid4()}"
    nombre_completo = f"{payload.nombres} {payload.apellidos}".strip()

    profile = Profile(
        firebase_uid=firebase_uid,
        email=email,
        nombre_completo=nombre_completo,
        nombres=payload.nombres,
        apellidos=payload.apellidos,
        fecha_nacimiento=payload.fecha_nacimiento,
        username=username,
    )
    db.add(profile)

    user = db.get(User, firebase_uid)
    if user is None:
        user = User(id=firebase_uid, email=email, nombre=nombre_completo)
        db.add(user)

    db.flush()

    credential = LocalCredential(profile_id=profile.id, password_hash=hash_password(payload.password))
    db.add(credential)
    db.flush()

    return LocalUserRead.model_validate(profile, from_attributes=True)


@router.post("/login", response_model=LocalUserRead)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LocalUserRead:
    identifier = _normalize(payload.identificador)

    profile_stmt = (
        select(Profile)
        .join(LocalCredential, LocalCredential.profile_id == Profile.id)
        .where(
            or_(
                func.lower(Profile.email) == identifier,
                func.lower(Profile.username) == identifier,
            )
        )
    )
    profile = db.execute(profile_stmt).scalar_one_or_none()

    if profile is None or profile.local_credential is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    if not verify_password(payload.password, profile.local_credential.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    now = datetime.now(timezone.utc)
    profile.local_credential.ultimo_login = now

    user = db.get(User, profile.firebase_uid)
    if user is not None:
        user.ultimo_acceso = now

    return LocalUserRead.model_validate(profile, from_attributes=True)


@router.post(
    "/recover-password",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def recover_password(
    payload: PasswordRecoveryRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    identifier = _normalize(payload.identificador)
    profile_stmt = (
        select(Profile)
        .join(LocalCredential, LocalCredential.profile_id == Profile.id)
        .where(
            or_(
                func.lower(Profile.email) == identifier,
                func.lower(Profile.username) == identifier,
            )
        )
    )
    profile = db.execute(profile_stmt).scalar_one_or_none()

    if profile and profile.local_credential:
        now = datetime.now(timezone.utc)

        for existing in profile.password_reset_tokens:
            if existing.usado_en is None and existing.expires_at > now:
                existing.usado_en = now
        reset_token = PasswordResetToken(
            profile_id=profile.id,
            token=token_urlsafe(32),
            expires_at=now + timedelta(hours=1),
        )
        db.add(reset_token)
        db.flush()

        send_password_reset_email(profile.email, reset_token.token)

    return MessageResponse(detail="Si la cuenta existe, enviaremos instrucciones para restablecer la contraseña")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
)
def reset_password(
    payload: PasswordResetConfirmRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    token_stmt = (
        select(PasswordResetToken)
        .options()
        .where(PasswordResetToken.token == payload.token)
    )
    reset_token = db.execute(token_stmt).scalar_one_or_none()
    if reset_token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token de recuperación inválido")

    if reset_token.usado_en is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token de recuperación inválido")

    if reset_token.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token de recuperación expirado")

    profile = reset_token.profile

    if profile.local_credential is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La cuenta no permite restablecimiento local")

    profile.local_credential.password_hash = hash_password(payload.password)

    now = datetime.now(timezone.utc)
    reset_token.usado_en = now

    for other in profile.password_reset_tokens:
        if other is not reset_token and other.usado_en is None:
            other.usado_en = now

    return MessageResponse(detail="Contraseña restablecida correctamente")
