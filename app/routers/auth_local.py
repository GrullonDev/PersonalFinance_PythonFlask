from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
import logging
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.local_credential import LocalCredential
from app.models.password_reset_token import PasswordResetToken
from app.models.profile import Profile
from app.models.user import User
from app.schema.auth import (
    LocalLoginResponse,
    LocalUserRead,
    LoginRequest,
    MessageResponse,
    PasswordRecoveryRequest,
    PasswordResetConfirmRequest,
    RegisterRequest,
)
from app.services.email import send_password_reset_email
from app.services.local_token import create_local_access_token
from app.services.security import hash_password, verify_password


router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)


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

    firebase_uid_candidate = payload.normalized_firebase_uid()
    if firebase_uid_candidate is not None:
        firebase_uid = firebase_uid_candidate
        if not firebase_uid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El Firebase UID no puede estar vacío",
            )

        firebase_exists_stmt = select(Profile.id).where(Profile.firebase_uid == firebase_uid)
        if db.execute(firebase_exists_stmt).scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un usuario con ese Firebase UID",
            )
    else:
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
    else:
        user.email = email or user.email
        user.nombre = nombre_completo or user.nombre

    db.flush()

    credential = LocalCredential(profile_id=profile.id, password_hash=hash_password(payload.password))
    db.add(credential)
    db.flush()

    return LocalUserRead.model_validate(profile, from_attributes=True)


@router.post("/login", response_model=LocalLoginResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> LocalLoginResponse:
    email = payload.normalized_email()

    profile_stmt = select(Profile).where(func.lower(Profile.email) == email)
    profile = db.execute(profile_stmt).scalar_one_or_none()
    if profile is not None:
        db.refresh(profile, attribute_names=["local_credential"])

    if profile is None or profile.local_credential is None:
        logger.warning("Profile or credentials missing for email=%s", email)
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Credenciales inválidas"})

    if not verify_password(payload.password, profile.local_credential.password_hash):
        logger.warning("Password mismatch for profile_id=%s", profile.id)
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Credenciales inválidas"})

    now = datetime.now(timezone.utc)
    profile.local_credential.ultimo_login = now

    user = db.get(User, profile.firebase_uid)
    if user is not None:
        user.ultimo_acceso = now

    user_read = LocalUserRead.model_validate(profile, from_attributes=True)
    access_token = create_local_access_token(
        firebase_uid=profile.firebase_uid,
        email=profile.email,
        nombre=profile.nombre_completo,
    )

    response_payload = LocalLoginResponse(access_token=access_token, token_type="bearer", user=user_read)
    # Deja que FastAPI serialice el modelo (maneja datetimes). Solo añadimos el header.
    response.headers["Authorization"] = f"Bearer {access_token}"
    return response_payload


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

    now = datetime.now(timezone.utc)
    expires_at = reset_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token de recuperación expirado")

    profile = reset_token.profile

    if profile.local_credential is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La cuenta no permite restablecimiento local")

    profile.local_credential.password_hash = hash_password(payload.password)
    db.add(profile.local_credential)
    db.flush()

    reset_token.usado_en = now

    for other in profile.password_reset_tokens:
        if other is not reset_token and other.usado_en is None:
            other.usado_en = now

    return MessageResponse(detail="Contraseña restablecida correctamente")
