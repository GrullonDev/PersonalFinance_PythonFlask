from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from fastapi import HTTPException, status

from app.core.config import settings

ALGORITHM = "HS256"


def create_local_access_token(*, firebase_uid: str, email: str | None, nombre: str | None) -> str:
    """Genera un JWT firmado que identifica al usuario local."""
    secret = settings.LOCAL_AUTH_SECRET
    if not secret:
        raise RuntimeError("LOCAL_AUTH_SECRET is not configurado; define una clave para firmar tokens locales.")

    now = datetime.now(timezone.utc)
    expires_delta = timedelta(minutes=settings.LOCAL_AUTH_TOKEN_EXPIRES_MINUTES)
    payload: Dict[str, Any] = {
        "uid": firebase_uid,
        "email": email,
        "name": nombre,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "token_type": "local",
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def try_decode_local_token(token: str) -> Dict[str, Any] | None:
    """Devuelve el payload si el token pertenece al backend local; None si no aplica."""
    secret = settings.LOCAL_AUTH_SECRET
    if not secret:
        return None

    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token local expirado") from exc
    except jwt.InvalidTokenError:
        return None

    if payload.get("token_type") != "local":
        return None
    if "uid" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token local inválido")
    return payload
