"""Pruebas de integración de endpoints HTTP y aislamiento entre usuarios con TestClient."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.models.base import Base, get_db

# Motor SQLite en memoria aislado para pruebas de integración de API
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module")
def client():
    """Configura cliente de pruebas con base de datos SQLite en memoria limpia."""
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


def test_api_user_registration_and_login(client: TestClient) -> None:
    """Verifica registro e inicio de sesión vía HTTP."""
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={"username": "alice_api", "email": "alice_api@example.com", "password": "Password123!"},
    )
    assert reg_resp.status_code == 201
    assert reg_resp.json()["username"] == "alice_api"

    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "alice_api", "password": "Password123!"},
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


def test_api_isolation_between_users(client: TestClient) -> None:
    """Verifica que un token de Usuario B no puede leer ni mutar productos de Usuario A vía API."""
    # 1. Registrar y loguear Usuario A
    client.post(
        "/api/v1/auth/register",
        json={"username": "user_a", "email": "user_a@example.com", "password": "Password123!"},
    )
    token_a = client.post(
        "/api/v1/auth/login",
        data={"username": "user_a", "password": "Password123!"},
    ).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Registrar y loguear Usuario B
    client.post(
        "/api/v1/auth/register",
        json={"username": "user_b", "email": "user_b@example.com", "password": "Password123!"},
    )
    token_b = client.post(
        "/api/v1/auth/login",
        data={"username": "user_b", "password": "Password123!"},
    ).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Usuario A crea un producto
    create_resp = client.post(
        "/api/v1/products",
        headers=headers_a,
        json={"name": "Teclado Mecánico", "cantidad_disponible": 5, "cantidad_minima": 2},
    )
    assert create_resp.status_code == 201
    prod_a_id = create_resp.json()["id"]

    # 4. Usuario B intenta acceder directamente al producto de A -> 404 Not Found
    get_alien = client.get(f"/api/v1/products/{prod_a_id}", headers=headers_b)
    assert get_alien.status_code == 404

    # 5. Usuario B intenta editar el producto de A -> 404 Not Found
    put_alien = client.put(
        f"/api/v1/products/{prod_a_id}",
        headers=headers_b,
        json={"name": "Teclado Hackeado"},
    )
    assert put_alien.status_code == 404

    # 6. Usuario B intenta ajustar existencias del producto de A -> 404 Not Found
    adjust_alien = client.post(
        f"/api/v1/products/{prod_a_id}/adjust-stock",
        headers=headers_b,
        json={"nueva_cantidad_disponible": 0},
    )
    assert adjust_alien.status_code == 404

    # 7. Usuario B intenta borrar el producto de A -> 404 Not Found
    del_alien = client.delete(f"/api/v1/products/{prod_a_id}", headers=headers_b)
    assert del_alien.status_code == 404

    # 8. Usuario B lista sus productos -> la lista no contiene el producto de A
    list_b = client.get("/api/v1/products", headers=headers_b).json()
    assert list_b["total"] == 0
    assert len(list_b["items"]) == 0


def test_api_duplicate_name_error_handling(client: TestClient) -> None:
    """Verifica que crear un producto duplicado devuelva HTTP 400 controlado y sin error 500."""
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "user_a", "password": "Password123!"},
    )
    if login_resp.status_code != 200:
        client.post(
            "/api/v1/auth/register",
            json={"username": "user_a", "email": "user_a@example.com", "password": "Password123!"},
        )
        login_resp = client.post(
            "/api/v1/auth/login",
            data={"username": "user_a", "password": "Password123!"},
        )

    token_a = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token_a}"}

    # Asegurar que el producto inicial exista
    client.post(
        "/api/v1/products",
        headers=headers,
        json={"name": "Teclado Mecánico", "cantidad_disponible": 5, "cantidad_minima": 2},
    )

    resp = client.post(
        "/api/v1/products",
        headers=headers,
        json={"name": "Teclado Mecánico", "cantidad_disponible": 10, "cantidad_minima": 1},
    )
    assert resp.status_code == 400
    assert "ya existe un producto" in resp.json()["detail"].lower()


def test_api_delete_product_confirmation_and_isolation(client: TestClient) -> None:
    """Verifica FR-012: eliminación exige confirmación explícita del servidor y mantiene aislamiento."""
    # Autenticar usuario propietario
    login_a = client.post(
        "/api/v1/auth/login",
        data={"username": "user_a", "password": "Password123!"},
    )
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Autenticar usuario ajeno
    login_b = client.post(
        "/api/v1/auth/login",
        data={"username": "user_b", "password": "Password123!"},
    )
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Crear producto para user_a
    create_resp = client.post(
        "/api/v1/products",
        headers=headers_a,
        json={"name": "Monitor Curvo 34", "cantidad_disponible": 4, "cantidad_minima": 1},
    )
    assert create_resp.status_code == 201
    prod_id = create_resp.json()["id"]

    # 2. Intento de eliminación sin parámetro confirm (por defecto False) -> 400 Bad Request
    del_no_param = client.delete(f"/api/v1/products/{prod_id}", headers=headers_a)
    assert del_no_param.status_code == 400
    assert "confirmación explícita" in del_no_param.json()["detail"].lower()

    # 3. Intento de eliminación con confirm=false -> 400 Bad Request
    del_false = client.delete(f"/api/v1/products/{prod_id}?confirm=false", headers=headers_a)
    assert del_false.status_code == 400
    assert "confirmación explícita" in del_false.json()["detail"].lower()

    # 4. El producto sigue existiendo
    check_exists = client.get(f"/api/v1/products/{prod_id}", headers=headers_a)
    assert check_exists.status_code == 200

    # 5. Usuario ajeno intenta borrar con confirm=true -> 404 Not Found (aislamiento estricto)
    del_alien = client.delete(f"/api/v1/products/{prod_id}?confirm=true", headers=headers_b)
    assert del_alien.status_code == 404

    # 6. Eliminación con confirm=true por el propietario -> 204 No Content
    del_confirmed = client.delete(f"/api/v1/products/{prod_id}?confirm=true", headers=headers_a)
    assert del_confirmed.status_code == 204

    # 7. Comprobar que ya no existe
    check_deleted = client.get(f"/api/v1/products/{prod_id}", headers=headers_a)
    assert check_deleted.status_code == 404
