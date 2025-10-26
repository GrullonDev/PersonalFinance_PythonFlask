import pytest
from fastapi.testclient import TestClient


def test_request_without_token_returns_401(client: TestClient):
    response = client.get("/api/v1/categories/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Falta encabezado Authorization: Bearer <token>"


def test_request_with_blank_token_returns_401(client: TestClient):
    response = client.get("/api/v1/categories/", headers={"Authorization": "Bearer   "})
    assert response.status_code == 401
    assert response.json()["detail"] == "Token de autenticación vacío"


def test_token_without_uid_returns_401(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    def fake_verify(_: str) -> dict:
        return {}

    monkeypatch.setattr("app.deps.auth.verify_firebase_token", fake_verify)

    response = client.get("/api/v1/categories/", headers={"Authorization": "Bearer token-without-uid"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Token de Firebase sin UID"


def test_token_without_email_not_allowed_when_test_tokens_disabled(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
):
    def fake_verify(_: str) -> dict:
        return {"uid": "user-no-email"}

    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "ALLOW_TEST_TOKENS", False, raising=False)
    monkeypatch.setattr("app.deps.auth.settings.ALLOW_TEST_TOKENS", False, raising=False)

    monkeypatch.setattr("app.deps.auth.verify_firebase_token", fake_verify)

    client: TestClient = request.getfixturevalue("client")
    response = client.get("/api/v1/categories/", headers={"Authorization": "Bearer user-no-email"})
    assert response.status_code == 400
    assert response.json()["detail"] == "El token no incluye email; no se puede enlazar el perfil"
