"""Script de verificación integral del servidor MCP y sus herramientas.

Verifica:
1. Inicio y disponibilidad del servidor MCP tanto en memoria como por proceso stdio independiente.
2. Ejecución real de 'consultar_inventario' y 'consultar_productos_stock_bajo' con base de datos real.
3. Detección precisa del producto con stock bajo (disponible <= minima) y cálculo de deficiencia.
4. Respeto estricto a la identidad del usuario y aislamiento total entre usuarios diferentes.
5. Manejo seguro de tokens inválidos.
6. Ocultamiento de tokens y contraseñas en los reportes de salida.
"""

import asyncio
import json
import sys
from typing import Any, Dict

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from src.models.base import Base, SessionLocal, engine
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository
from src.schemas.auth import UserRegisterRequest
from src.schemas.product import ProductCreateRequest
from src.services.auth_service import AuthService
from src.services.product_service import ProductService
from src.mcp.server import mcp


def redact_data(obj: Any) -> Any:
    """Oculta tokens y contraseñas en estructuras de datos para visualización segura."""
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            if k.lower() in ("token", "access_token", "password", "hashed_password", "secret"):
                new_dict[k] = "[TOKEN_OCULTO]" if "token" in k.lower() else "[PASSWORD_OCULTO]"
            else:
                new_dict[k] = redact_data(v)
        return new_dict
    elif isinstance(obj, list):
        return [redact_data(item) for item in obj]
    return obj


def setup_test_environment():
    """Configura usuarios y productos de prueba en la base de datos real."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        product_repo = ProductRepository(db)
        auth_service = AuthService(user_repository=user_repo)
        product_service = ProductService(product_repository=product_repo)

        # Usuario 1 de prueba (Alice)
        u1_name = "test_user_a"
        u1_email = "test_a@example.com"
        u1_pwd = "TestPassword123!"

        user_1 = user_repo.get_by_username(u1_name)
        if not user_1:
            user_1 = auth_service.register_user(
                UserRegisterRequest(username=u1_name, email=u1_email, password=u1_pwd)
            )

        # Usuario 2 de prueba (Bob)
        u2_name = "test_user_b"
        u2_email = "test_b@example.com"
        u2_pwd = "TestPassword456!"

        user_2 = user_repo.get_by_username(u2_name)
        if not user_2:
            user_2 = auth_service.register_user(
                UserRegisterRequest(username=u2_name, email=u2_email, password=u2_pwd)
            )

        # Limpiar productos existentes de los usuarios de prueba para garantizar idempotencia
        for p in product_repo.list_by_user(user_1.id, limit=100):
            product_repo.delete(p)
        for p in product_repo.list_by_user(user_2.id, limit=100):
            product_repo.delete(p)

        # Crear productos para Usuario 1:
        # Producto 1.1: Stock normal (disponible: 25 > minima: 10)
        product_service.create_product(
            user_id=user_1.id,
            request=ProductCreateRequest(
                name="Arroz Extra 1kg",
                description="Arroz de grano largo",
                cantidad_disponible=25,
                cantidad_minima=10,
            ),
        )
        # Producto 1.2: Stock bajo (disponible: 2 <= minima: 5) -> Alerta activa, deficiencia: 3
        product_service.create_product(
            user_id=user_1.id,
            request=ProductCreateRequest(
                name="Aceite Vegetal 1L",
                description="Aceite para cocinar",
                cantidad_disponible=2,
                cantidad_minima=5,
            ),
        )

        # Crear producto para Usuario 2:
        # Producto 2.1: Stock bajo de Bob (disponible: 1 <= minima: 4) -> Alerta activa, deficiencia: 3
        product_service.create_product(
            user_id=user_2.id,
            request=ProductCreateRequest(
                name="Café Colombiano 500g",
                description="Café tostado molido",
                cantidad_disponible=1,
                cantidad_minima=4,
            ),
        )

        # Autenticar usuarios y obtener tokens JWT
        token_u1 = auth_service.authenticate_user(u1_name, u1_pwd).access_token
        token_u2 = auth_service.authenticate_user(u2_name, u2_pwd).access_token

        return token_u1, token_u2, u1_name, u2_name
    finally:
        db.close()


async def run_mcp_tests():
    print("=" * 80)
    print("VERIFICACIÓN REAL DEL SERVIDOR MCP (Model Context Protocol)")
    print("=" * 80)

    token_u1, token_u2, u1_name, u2_name = setup_test_environment()
    print("\n[OK] Datos de prueba configurados en la base de datos real (inventario.db):")
    print(f"  * Usuario A: '{u1_name}' con credenciales válidas y Token: [TOKEN_OCULTO]")
    print(f"      - 'Arroz Extra 1kg': disponible=25, minima=10 (Stock Normal)")
    print(f"      - 'Aceite Vegetal 1L': disponible=2, minima=5 (Stock Bajo, Deficiencia=3)")
    print(f"  * Usuario B: '{u2_name}' con credenciales válidas y Token: [TOKEN_OCULTO]")
    print(f"      - 'Café Colombiano 500g': disponible=1, minima=4 (Stock Bajo, Deficiencia=3)")

    # -------------------------------------------------------------------------
    # PARTE 1: Verificación de FastMCP en memoria
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("FASE 1: VERIFICACIÓN DEL REGISTRO DE HERRAMIENTAS EN FASTMCP")
    print("=" * 80)
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    print(f"Nombre del servidor FastMCP : {mcp.name}")
    print(f"Herramientas expuestas       : {tool_names}")
    assert "consultar_inventario" in tool_names, "Herramienta 'consultar_inventario' no encontrada"
    assert "consultar_productos_stock_bajo" in tool_names, "Herramienta 'consultar_productos_stock_bajo' no encontrada"
    print("[OK] Ambas herramientas requeridas están correctamente registradas.")

    # -------------------------------------------------------------------------
    # PARTE 2: Conexión y ejecución vía subproceso stdio (servidor real en vivo)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("FASE 2: EJECUCIÓN EN VIVO DEL SERVIDOR MCP VÍA PROCESO STDIO INDEPENDIENTE")
    print("Comando del servidor: python -m src.mcp.server")
    print("=" * 80)

    server_params = StdioServerParameters(command=sys.executable, args=["-m", "src.mcp.server"])

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("[OK] Sesión MCP cliente-servidor inicializada exitosamente sobre stdio.")

            # -----------------------------------------------------------------
            # 2.1 Herramienta 'consultar_inventario' para Usuario A
            # -----------------------------------------------------------------
            print("\n" + "-" * 75)
            print("1. Invocando 'consultar_inventario' con token de Usuario A")
            print("   Parámetros: {'token': '[TOKEN_OCULTO]'}")
            print("-" * 75)
            res_inv_a = await session.call_tool("consultar_inventario", {"token": token_u1})
            data_inv_a = res_inv_a.structured_content
            print("Respuesta del Servidor MCP:")
            print(json.dumps(redact_data(data_inv_a), indent=2, ensure_ascii=False))

            assert data_inv_a["status"] == "success"
            assert data_inv_a["usuario"] == u1_name
            assert data_inv_a["total_productos"] == 2
            assert data_inv_a["total_stock_bajo"] == 1
            nombres_u1 = [p["nombre"] for p in data_inv_a["productos"]]
            assert "Arroz Extra 1kg" in nombres_u1
            assert "Aceite Vegetal 1L" in nombres_u1
            assert "Café Colombiano 500g" not in nombres_u1, "Violación de identidad: producto ajeno visible"
            print("-> ASERCIÓN EXITOSA: Solo retorna los productos de Usuario A.")

            # -----------------------------------------------------------------
            # 2.2 Herramienta 'consultar_productos_stock_bajo' para Usuario A
            # -----------------------------------------------------------------
            print("\n" + "-" * 75)
            print("2. Invocando 'consultar_productos_stock_bajo' con token de Usuario A")
            print("   Parámetros: {'token': '[TOKEN_OCULTO]'}")
            print("-" * 75)
            res_crit_a = await session.call_tool("consultar_productos_stock_bajo", {"token": token_u1})
            data_crit_a = res_crit_a.structured_content
            print("Respuesta del Servidor MCP:")
            print(json.dumps(redact_data(data_crit_a), indent=2, ensure_ascii=False))

            assert data_crit_a["status"] == "success"
            assert data_crit_a["usuario"] == u1_name
            assert data_crit_a["productos_criticos_count"] == 1
            criticos = data_crit_a["productos_criticos"]
            assert len(criticos) == 1
            assert criticos[0]["nombre"] == "Aceite Vegetal 1L"
            assert criticos[0]["deficiencia"] == 3
            # Validar que NO incluye el de stock normal ni de otro usuario
            assert "Arroz Extra 1kg" not in [p["nombre"] for p in criticos]
            assert "Café Colombiano 500g" not in [p["nombre"] for p in criticos]
            print("-> ASERCIÓN EXITOSA: Detectó únicamente el producto con stock bajo ('Aceite Vegetal 1L') con deficiencia = 3.")

            # -----------------------------------------------------------------
            # 2.3 Respeto a la identidad y aislamiento con Usuario B
            # -----------------------------------------------------------------
            print("\n" + "-" * 75)
            print("3. Invocando 'consultar_inventario' con token de Usuario B")
            print("   Parámetros: {'token': '[TOKEN_OCULTO]'}")
            print("-" * 75)
            res_inv_b = await session.call_tool("consultar_inventario", {"token": token_u2})
            data_inv_b = res_inv_b.structured_content
            print("Respuesta del Servidor MCP:")
            print(json.dumps(redact_data(data_inv_b), indent=2, ensure_ascii=False))

            assert data_inv_b["status"] == "success"
            assert data_inv_b["usuario"] == u2_name
            assert data_inv_b["total_productos"] == 1
            assert data_inv_b["productos"][0]["nombre"] == "Café Colombiano 500g"
            # Verificar ausencia de productos de Usuario A
            for p in data_inv_b["productos"]:
                assert p["nombre"] not in ["Arroz Extra 1kg", "Aceite Vegetal 1L"]
            print("-> ASERCIÓN EXITOSA: Usuario B solo ve su propio inventario.")

            print("\n" + "-" * 75)
            print("4. Invocando 'consultar_productos_stock_bajo' con token de Usuario B")
            print("   Parámetros: {'token': '[TOKEN_OCULTO]'}")
            print("-" * 75)
            res_crit_b = await session.call_tool("consultar_productos_stock_bajo", {"token": token_u2})
            data_crit_b = res_crit_b.structured_content
            print("Respuesta del Servidor MCP:")
            print(json.dumps(redact_data(data_crit_b), indent=2, ensure_ascii=False))

            assert data_crit_b["status"] == "success"
            assert data_crit_b["usuario"] == u2_name
            assert data_crit_b["productos_criticos_count"] == 1
            assert data_crit_b["productos_criticos"][0]["nombre"] == "Café Colombiano 500g"
            assert data_crit_b["productos_criticos"][0]["deficiencia"] == 3
            print("-> ASERCIÓN EXITOSA: Detectó únicamente el stock crítico de Usuario B. Aislamiento total confirmado.")

            # -----------------------------------------------------------------
            # 2.4 Token inválido
            # -----------------------------------------------------------------
            print("\n" + "-" * 75)
            print("5. Invocando herramientas con Token Inválido")
            print("   Parámetros: {'token': '[TOKEN_INVALIDO_OCULTO]'}")
            print("-" * 75)
            res_bad = await session.call_tool("consultar_inventario", {"token": "token_invalido_prueba_123"})
            data_bad = res_bad.structured_content
            print("Respuesta del Servidor MCP ante token inválido:")
            print(json.dumps(redact_data(data_bad), indent=2, ensure_ascii=False))

            assert data_bad["status"] == "error"
            assert data_bad["error"] == "TOKEN_INVALIDO"
            print("-> ASERCIÓN EXITOSA: Manejo controlado y seguro de tokens inválidos.")

    print("\n" + "=" * 80)
    print("VERIFICACIÓN COMPLETA FINALIZADA CON ÉXITO")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_mcp_tests())
