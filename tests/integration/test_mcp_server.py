"""Pruebas de integración para el servidor MCP FastMCP."""

import pytest
from src.mcp.server import mcp
from src.models.base import Base, engine, SessionLocal
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository
from src.schemas.auth import UserRegisterRequest
from src.schemas.product import ProductCreateRequest
from src.services.auth_service import AuthService
from src.services.product_service import ProductService


@pytest.mark.anyio
async def test_fastmcp_server_tools_execution_and_isolation():
    """Valida la ejecución de herramientas MCP directamente desde el servidor FastMCP con BD real."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        prod_repo = ProductRepository(db)
        auth_service = AuthService(user_repo)
        prod_service = ProductService(prod_repo)

        # Configurar 2 usuarios
        u1 = user_repo.get_by_username("int_mcp_u1")
        if not u1:
            u1 = auth_service.register_user(
                UserRegisterRequest(username="int_mcp_u1", email="mcp1@test.com", password="Password123!")
            )
        u2 = user_repo.get_by_username("int_mcp_u2")
        if not u2:
            u2 = auth_service.register_user(
                UserRegisterRequest(username="int_mcp_u2", email="mcp2@test.com", password="Password123!")
            )

        # Limpiar productos previos
        for p in prod_repo.list_by_user(u1.id, limit=100):
            prod_repo.delete(p)
        for p in prod_repo.list_by_user(u2.id, limit=100):
            prod_repo.delete(p)

        # u1: 1 normal, 1 bajo stock
        prod_service.create_product(
            u1.id, ProductCreateRequest(name="Prod Normal", cantidad_disponible=20, cantidad_minima=5)
        )
        prod_service.create_product(
            u1.id, ProductCreateRequest(name="Prod Critico", cantidad_disponible=1, cantidad_minima=4)
        )

        # u2: 1 bajo stock
        prod_service.create_product(
            u2.id, ProductCreateRequest(name="Prod U2", cantidad_disponible=2, cantidad_minima=6)
        )

        token_u1 = auth_service.authenticate_user("int_mcp_u1", "Password123!").access_token
        token_u2 = auth_service.authenticate_user("int_mcp_u2", "Password123!").access_token

        # Test consultar_inventario u1
        res_inv = await mcp.call_tool("consultar_inventario", {"token": token_u1})
        inv_data = res_inv.structured_content
        assert inv_data["status"] == "success"
        assert inv_data["usuario"] == "int_mcp_u1"
        assert inv_data["total_productos"] == 2
        assert inv_data["total_stock_bajo"] == 1
        nombres = [p["nombre"] for p in inv_data["productos"]]
        assert "Prod Normal" in nombres
        assert "Prod Critico" in nombres
        assert "Prod U2" not in nombres

        # Test consultar_productos_stock_bajo u1
        res_crit = await mcp.call_tool("consultar_productos_stock_bajo", {"token": token_u1})
        crit_data = res_crit.structured_content
        assert crit_data["status"] == "success"
        assert crit_data["usuario"] == "int_mcp_u1"
        assert crit_data["productos_criticos_count"] == 1
        assert len(crit_data["productos_criticos"]) == 1
        assert crit_data["productos_criticos"][0]["nombre"] == "Prod Critico"
        assert crit_data["productos_criticos"][0]["deficiencia"] == 3

        # Test consultar_inventario u2
        res_inv_u2 = await mcp.call_tool("consultar_inventario", {"token": token_u2})
        inv_u2_data = res_inv_u2.structured_content
        assert inv_u2_data["usuario"] == "int_mcp_u2"
        assert inv_u2_data["total_productos"] == 1
        assert inv_u2_data["productos"][0]["nombre"] == "Prod U2"

        # Test invalid token
        res_err = await mcp.call_tool("consultar_inventario", {"token": "invalido"})
        assert res_err.structured_content["status"] == "error"
        assert res_err.structured_content["error"] == "TOKEN_INVALIDO"

    finally:
        db.close()
