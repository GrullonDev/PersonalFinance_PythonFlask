from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_profile_created_on_first_request(client: TestClient):
    response = client.get("/api/v1/profiles/me", headers=auth_headers("user-123"))
    assert response.status_code == 200

    payload = response.json()
    assert payload["firebase_uid"] == "user-123"
    assert payload["email"] == "user-123@local.dev"
    assert payload["nombre_completo"] == "user-123"
    assert payload["id"] is not None
    assert payload["fecha_creacion"] is not None


def test_category_unique_constraint(client: TestClient):
    headers = auth_headers("user-categories")
    body = {"nombre": "Transporte", "tipo": "gasto"}

    first = client.post("/api/v1/categories/", json=body, headers=headers)
    assert first.status_code == 201

    duplicate = client.post("/api/v1/categories/", json=body, headers=headers)
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Ya existe una categoría con ese nombre y tipo"


def test_budget_date_validation(client: TestClient):
    headers = auth_headers("user-budget")
    invalid_payload = {
        "nombre": "Q1 ahorro",
        "monto_total": "5000.00",
        "fecha_inicio": date.today().isoformat(),
        "fecha_fin": (date.today() - timedelta(days=1)).isoformat(),
    }

    response = client.post("/api/v1/budgets/", json=invalid_payload, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "La fecha de fin debe ser mayor o igual a la fecha de inicio"


def test_transaction_requires_owned_category(client: TestClient):
    headers_user_one = auth_headers("user-one")
    headers_user_two = auth_headers("user-two")

    category_one = client.post(
        "/api/v1/categories/",
        json={"nombre": "Salario", "tipo": "ingreso"},
        headers=headers_user_one,
    )
    assert category_one.status_code == 201
    category_two = client.post(
        "/api/v1/categories/",
        json={"nombre": "Regalos", "tipo": "ingreso"},
        headers=headers_user_two,
    )
    assert category_two.status_code == 201

    foreign_category_id = category_two.json()["id"]
    payload = {
        "tipo": "ingreso",
        "monto": "1200.00",
        "descripcion": "Pago mensual",
        "fecha": date.today().isoformat(),
        "categoria_id": foreign_category_id,
        "es_recurrente": False,
    }

    response = client.post("/api/v1/transactions/", json=payload, headers=headers_user_one)
    assert response.status_code == 400
    assert response.json()["detail"] == "La categoría no pertenece al usuario autenticado"


def test_budget_duplicate_range_rejected(client: TestClient):
    headers = auth_headers("user-budget-dup")
    payload = {
        "nombre": "Mes actual",
        "monto_total": "2500.00",
        "fecha_inicio": date(2024, 5, 1).isoformat(),
        "fecha_fin": date(2024, 5, 31).isoformat(),
    }

    first = client.post("/api/v1/budgets/", json=payload, headers=headers)
    assert first.status_code == 201

    duplicate = client.post("/api/v1/budgets/", json=payload, headers=headers)
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Ya existe un presupuesto con ese nombre y rango de fechas"


def test_transaction_update_rejects_foreign_category(client: TestClient):
    headers_user_one = auth_headers("update-user")
    headers_user_two = auth_headers("update-user-2")

    category_one = client.post(
        "/api/v1/categories/",
        json={"nombre": "Ventas", "tipo": "ingreso"},
        headers=headers_user_one,
    )
    category_two = client.post(
        "/api/v1/categories/",
        json={"nombre": "Regalo", "tipo": "ingreso"},
        headers=headers_user_two,
    )
    assert category_one.status_code == 201
    assert category_two.status_code == 201

    transaction_payload = {
        "tipo": "ingreso",
        "monto": "1500.00",
        "descripcion": "Venta especial",
        "fecha": date.today().isoformat(),
        "categoria_id": category_one.json()["id"],
        "es_recurrente": False,
    }
    transaction = client.post("/api/v1/transactions/", json=transaction_payload, headers=headers_user_one)
    assert transaction.status_code == 201

    update = client.put(
        f"/api/v1/transactions/{transaction.json()['id']}",
        json={"categoria_id": category_two.json()["id"]},
        headers=headers_user_one,
    )
    assert update.status_code == 400
    assert update.json()["detail"] == "La categoría no pertenece al usuario autenticado"
