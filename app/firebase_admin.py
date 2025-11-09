import logging
from functools import lru_cache
from typing import Any, Dict

import firebase_admin
from fastapi import HTTPException, status
from firebase_admin import auth, credentials

from app.core.config import settings
from app.services.local_token import try_decode_local_token

logger = logging.getLogger(__name__)


@lru_cache
def _initialize_firebase_app() -> firebase_admin.App:
    """Initialize Firebase Admin SDK once per process."""
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    credential_path = settings.FIREBASE_CREDENTIALS_PATH
    if not credential_path:
        raise RuntimeError(
            "FIREBASE_CREDENTIALS_PATH is not configured. "
            "Define it or habilita ALLOW_TEST_TOKENS para entornos de desarrollo."
        )

    cred = credentials.Certificate(credential_path)
    options: Dict[str, Any] = {}
    if settings.FIREBASE_PROJECT_ID:
        options["projectId"] = settings.FIREBASE_PROJECT_ID

    logger.info("Inicializando Firebase Admin SDK")
    return firebase_admin.initialize_app(cred, options or None)


def verify_firebase_token(token: str) -> Dict[str, Any]:
    """Validate Firebase JWT and return decoded claims."""
    local_payload = try_decode_local_token(token)
    if local_payload is not None:
        return local_payload

    if settings.ALLOW_TEST_TOKENS and settings.ENVIRONMENT != "production":
        # Permite usar el propio token como UID en desarrollo/test (p.ej. 'test-uid-123')
        return {"uid": token}

    _initialize_firebase_app()

    try:
        return auth.verify_id_token(token, check_revoked=True)
    except auth.ExpiredIdTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token expirado",
        ) from exc
    except auth.InvalidIdTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token inválido",
        ) from exc
    except Exception as exc:  # pragma: no cover - defensivo
        logger.exception("Error verificando token de Firebase")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No fue posible validar el token de autenticación",
        ) from exc
