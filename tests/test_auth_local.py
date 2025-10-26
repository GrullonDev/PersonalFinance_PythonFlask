from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.local_credential import LocalCredential
from app.models.password_reset_token import PasswordResetToken
from app.models.profile import Profile


def _registration_payload(**overrides: object) -> dict[str, object]:
    payload = {
        "nombres": "Ana",
        "apellidos": "Pérez",
        "fecha_nacimiento": date(1990, 5, 21).isoformat(),
        "username": "ana.perez",
        "email": "ana@example.com",
        "email_confirmacion": "ana@example.com",
        "password": "S3gura!123",
        "password_confirmacion": "S3gura!123",
    }
    payload.update(overrides)
    return payload


def test_register_creates_profile_and_credentials(client: TestClient, db_session: Session):
    response = client.post("/api/v1/auth/register", json=_registration_payload())
    assert response.status_code == 201
    data = response.json()

    assert data["email"] == "ana@example.com"
    assert data["username"] == "ana.perez"
    assert data["nombres"] == "Ana"
    assert data["apellidos"] == "Pérez"
    assert data["nombre_completo"] == "Ana Pérez"

    profile = db_session.get(Profile, data["id"])
    assert profile is not None
    assert profile.local_credential is not None
    assert profile.local_credential.password_hash != "S3gura!123"


def test_register_rejects_duplicate_email(client: TestClient):
    payload = _registration_payload()
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    duplicate_email = _registration_payload(username="ana.diferente")
    response_dup = client.post("/api/v1/auth/register", json=duplicate_email)
    assert response_dup.status_code == 409
    assert response_dup.json()["detail"] == "Ya existe un usuario con ese email"


def test_register_rejects_duplicate_username(client: TestClient):
    payload = _registration_payload()
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    duplicate_username = _registration_payload(email="otra@example.com", email_confirmacion="otra@example.com")
    response_dup = client.post("/api/v1/auth/register", json=duplicate_username)
    assert response_dup.status_code == 409
    assert response_dup.json()["detail"] == "Ya existe un usuario con ese nombre de usuario"


def test_login_accepts_username_and_email(client: TestClient, db_session: Session):
    payload = _registration_payload()
    register_response = client.post("/api/v1/auth/register", json=payload)
    profile_id = register_response.json()["id"]

    login_with_username = client.post(
        "/api/v1/auth/login",
        json={"identificador": payload["username"], "password": payload["password"]},
    )
    assert login_with_username.status_code == 200
    assert login_with_username.json()["id"] == profile_id

    login_with_email = client.post(
        "/api/v1/auth/login",
        json={"identificador": payload["email"], "password": payload["password"]},
    )
    assert login_with_email.status_code == 200

    credential = db_session.execute(
        select(LocalCredential).join(Profile).where(Profile.id == profile_id)
    ).scalar_one_or_none()
    assert credential is not None
    assert credential.ultimo_login is not None


def test_login_rejects_invalid_password(client: TestClient):
    payload = _registration_payload()
    client.post("/api/v1/auth/register", json=payload)

    response = client.post(
        "/api/v1/auth/login",
        json={"identificador": payload["username"], "password": "ContraseñaErrónea1"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"


def test_password_recovery_creates_token(client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch):
    payload = _registration_payload()
    register_response = client.post("/api/v1/auth/register", json=payload)
    profile_id = register_response.json()["id"]

    captured: dict[str, str] = {}

    def fake_send(email: str, token: str) -> None:
        captured["email"] = email
        captured["token"] = token

    monkeypatch.setattr("app.routers.auth_local.send_password_reset_email", fake_send)

    response = client.post(
        "/api/v1/auth/recover-password",
        json={"identificador": payload["email"]},
    )
    assert response.status_code == 202

    tokens = db_session.execute(
        select(PasswordResetToken).join(Profile).where(Profile.id == profile_id)
    ).scalars().all()
    assert len(tokens) == 1
    assert tokens[0].token
    assert captured["email"] == payload["email"]
    assert captured["token"] == tokens[0].token


def test_password_recovery_is_silent_for_unknown_user(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("app.routers.auth_local.send_password_reset_email", lambda *_: None)

    response = client.post(
        "/api/v1/auth/recover-password",
        json={"identificador": "desconocido@example.com"},
    )
    assert response.status_code == 202
    assert response.json()["detail"] == "Si la cuenta existe, enviaremos instrucciones para restablecer la contraseña"
    tokens_count = db_session.execute(select(func.count()).select_from(PasswordResetToken)).scalar_one()
    assert tokens_count == 0


def test_password_reset_with_valid_token(client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch):
    payload = _registration_payload()
    client.post("/api/v1/auth/register", json=payload)

    captured: dict[str, str] = {}

    def fake_send(email: str, token: str) -> None:
        captured["email"] = email
        captured["token"] = token

    monkeypatch.setattr("app.routers.auth_local.send_password_reset_email", fake_send)

    client.post(
        "/api/v1/auth/recover-password",
        json={"identificador": payload["username"]},
    )

    token = captured["token"]
    new_password = "NuevaClave123!"
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": token,
            "password": new_password,
            "password_confirmacion": new_password,
        },
    )
    assert response.status_code == 200
    assert response.json()["detail"] == "Contraseña restablecida correctamente"

    login_old = client.post(
        "/api/v1/auth/login",
        json={"identificador": payload["email"], "password": payload["password"]},
    )
    assert login_old.status_code == 401

    login_new = client.post(
        "/api/v1/auth/login",
        json={"identificador": payload["email"], "password": new_password},
    )
    assert login_new.status_code == 200

    token_row = db_session.execute(
        select(PasswordResetToken).where(PasswordResetToken.token == token)
    ).scalar_one()
    assert token_row.usado_en is not None


def test_password_reset_invalid_token(client: TestClient):
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "token-invalido",
            "password": "ClaveSegura123",
            "password_confirmacion": "ClaveSegura123",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Token de recuperación inválido"
