"""Pruebas unitarias para herramientas MCP reutilizando servicios y validando identidad."""

from src.mcp.tools import consultar_inventario, consultar_productos_stock_bajo
from src.schemas.auth import UserRegisterRequest
from src.schemas.product import ProductCreateRequest
from src.services.auth_service import AuthService
from src.services.product_service import ProductService


def test_mcp_consultar_inventario_success(
    auth_service: AuthService, product_service: ProductService
) -> None:
    """Verifica la consulta exitosa de inventario vía MCP reutilizando servicios."""
    user = auth_service.register_user(
        UserRegisterRequest(username="mcp_user", email="mcp@example.com", password="Password123!")
    )
    token = auth_service.authenticate_user("mcp_user", "Password123!").access_token

    # Crear producto normal y producto con stock bajo
    product_service.create_product(
        user_id=user.id,
        request=ProductCreateRequest(name="Producto 1", cantidad_disponible=10, cantidad_minima=2),
    )
    product_service.create_product(
        user_id=user.id,
        request=ProductCreateRequest(name="Producto 2", cantidad_disponible=1, cantidad_minima=3),
    )

    result = consultar_inventario(
        token=token,
        auth_service=auth_service,
        product_service=product_service,
    )

    assert result["status"] == "success"
    assert result["usuario"] == "mcp_user"
    assert result["total_productos"] == 2
    assert result["total_stock_bajo"] == 1
    assert len(result["productos"]) == 2


def test_mcp_consultar_inventario_invalid_token(
    auth_service: AuthService, product_service: ProductService
) -> None:
    """Verifica que un token inválido sea rechazado de forma segura en MCP."""
    result = consultar_inventario(
        token="token_invalido_123",
        auth_service=auth_service,
        product_service=product_service,
    )

    assert result["status"] == "error"
    assert result["error"] == "TOKEN_INVALIDO"


def test_mcp_isolation_between_users(
    auth_service: AuthService, product_service: ProductService
) -> None:
    """Verifica que la herramienta MCP aísle estrictamente los productos de cada usuario."""
    u1 = auth_service.register_user(
        UserRegisterRequest(username="user1_mcp", email="u1@example.com", password="Password123!")
    )
    u2 = auth_service.register_user(
        UserRegisterRequest(username="user2_mcp", email="u2@example.com", password="Password123!")
    )

    token_u1 = auth_service.authenticate_user("user1_mcp", "Password123!").access_token
    token_u2 = auth_service.authenticate_user("user2_mcp", "Password123!").access_token

    product_service.create_product(
        user_id=u1.id, request=ProductCreateRequest(name="P_U1", cantidad_disponible=5, cantidad_minima=1)
    )
    product_service.create_product(
        user_id=u2.id, request=ProductCreateRequest(name="P_U2", cantidad_disponible=10, cantidad_minima=2)
    )

    res_u1 = consultar_inventario(token=token_u1, auth_service=auth_service, product_service=product_service)
    res_u2 = consultar_inventario(token=token_u2, auth_service=auth_service, product_service=product_service)

    assert res_u1["total_productos"] == 1
    assert res_u1["productos"][0]["nombre"] == "P_U1"

    assert res_u2["total_productos"] == 1
    assert res_u2["productos"][0]["nombre"] == "P_U2"


def test_mcp_consultar_productos_stock_bajo(
    auth_service: AuthService, product_service: ProductService
) -> None:
    """Verifica que la herramienta especializada devuelva únicamente productos en condición crítica."""
    user = auth_service.register_user(
        UserRegisterRequest(username="shopper", email="shopper@example.com", password="Password123!")
    )
    token = auth_service.authenticate_user("shopper", "Password123!").access_token

    product_service.create_product(
        user_id=user.id,
        request=ProductCreateRequest(name="Harina", cantidad_disponible=15, cantidad_minima=5),
    )
    product_service.create_product(
        user_id=user.id,
        request=ProductCreateRequest(name="Huevos", cantidad_disponible=2, cantidad_minima=6),
    )

    res = consultar_productos_stock_bajo(
        token=token,
        auth_service=auth_service,
        product_service=product_service,
    )

    assert res["status"] == "success"
    assert res["productos_criticos_count"] == 1
    assert len(res["productos_criticos"]) == 1
    assert res["productos_criticos"][0]["nombre"] == "Huevos"
    assert res["productos_criticos"][0]["deficiencia"] == 4
