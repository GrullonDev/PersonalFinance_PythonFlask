from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.firebase_admin import verify_firebase_token
from app.models.profile import Profile
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def _upsert_user(db: Session, firebase_uid: str, email: str | None, nombre: str | None) -> None:
    """Mantiene datos básicos del usuario en la tabla auxiliar users."""
    user = db.execute(select(User).where(User.id == firebase_uid)).scalar_one_or_none()
    if user is None:
        user = User(id=firebase_uid, email=email, nombre=nombre)
        db.add(user)
    else:
        user.email = email or user.email
        user.nombre = nombre or user.nombre


def get_current_profile(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Profile:
    """Obtiene el perfil autenticado a partir de un token Bearer de Firebase."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta encabezado Authorization: Bearer <token>",
        )

    token = credentials.credentials.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación vacío",
        )

    decoded_token = verify_firebase_token(token)
    firebase_uid = decoded_token.get("uid")
    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de Firebase sin UID",
        )

    email = decoded_token.get("email")
    display_name = decoded_token.get("name") or decoded_token.get("display_name")

    if not email:
        if settings.ALLOW_TEST_TOKENS and settings.ENVIRONMENT != "production":
            email = f"{firebase_uid}@local.dev"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El token no incluye email; no se puede enlazar el perfil",
            )

    nombre = display_name or email.split("@")[0]

    stmt = select(Profile).where(Profile.firebase_uid == firebase_uid)
    profile = db.execute(stmt).scalar_one_or_none()

    if profile is None:
        profile = Profile(firebase_uid=firebase_uid, email=email, nombre_completo=nombre)
        db.add(profile)
        db.flush()  # Necesario para obtener el ID antes de devolverlo
    else:
        # Mantiene datos sincronizados con Firebase
        profile.email = email
        profile.nombre_completo = nombre

    _upsert_user(db, firebase_uid=firebase_uid, email=email, nombre=nombre)

    return profile
