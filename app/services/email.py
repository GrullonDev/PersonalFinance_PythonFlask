from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_reset_link(token: str) -> str:
    if settings.PASSWORD_RESET_URL:
        if settings.PASSWORD_RESET_URL.endswith("="):
            return f"{settings.PASSWORD_RESET_URL}{token}"
        separator = "&" if "?" in settings.PASSWORD_RESET_URL else "?"
        return f"{settings.PASSWORD_RESET_URL}{separator}token={token}"
    return token


def send_password_reset_email(email: str, token: str) -> None:
    """Send a password reset message using SMTP settings, or log if unavailable."""
    if not settings.SMTP_HOST or not settings.EMAIL_SENDER:
        logger.info(
            "SMTP no configurado; se omite envío de email de recuperación para %s (token=%s)",
            email,
            token,
        )
        return

    message = EmailMessage()
    message["Subject"] = "Instrucciones para restablecer tu contraseña"
    message["From"] = settings.EMAIL_SENDER
    message["To"] = email

    reset_link = _build_reset_link(token)
    message.set_content(
        f"Hola,\n\n"
        f"Recibimos una solicitud para restablecer tu contraseña. "
        f"Utiliza el siguiente enlace o token dentro de la próxima hora:\n\n"
        f"{reset_link}\n\n"
        f"Si no solicitaste este cambio puedes ignorar este mensaje.\n"
    )

    port = settings.SMTP_PORT or (587 if settings.SMTP_USE_TLS else 25)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, port, timeout=30) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)
    except Exception:  # pragma: no cover - logging defensivo
        logger.exception("Fallo al enviar email de recuperación a %s", email)
        raise
