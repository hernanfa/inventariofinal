"""Implementación de herramientas Model Context Protocol (MCP) reutilizando servicios de dominio."""

from typing import Any, Dict, Optional
from src.models.base import Base, SessionLocal, engine
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService
from src.services.exceptions import AuthenticationError
from src.services.product_service import ProductService


def get_default_services():
    """Crea instancias de servicios conectadas a la base de datos por defecto para MCP."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    user_repo = UserRepository(db)
    product_repo = ProductRepository(db)
    auth_service = AuthService(user_repository=user_repo)
    product_service = ProductService(product_repository=product_repo)
    return auth_service, product_service


def consultar_inventario(
    token: str,
    solo_stock_bajo: bool = False,
    busqueda: Optional[str] = None,
    auth_service: Optional[AuthService] = None,
    product_service: Optional[ProductService] = None,
) -> Dict[str, Any]:
    """Consulta los productos del inventario del usuario autenticado, verificando identidad y aplicando filtros."""
    db_session = None
    if auth_service is None or product_service is None:
        default_auth, default_prod = get_default_services()
        auth_service = auth_service or default_auth
        product_service = product_service or default_prod
        db_session = getattr(auth_service.user_repository, "db", None)

    try:
        user = auth_service.get_user_from_token(token)
        items, total, total_low_stock = product_service.list_products(
            user_id=user.id,
            solo_stock_bajo=solo_stock_bajo,
            busqueda=busqueda,
        )

        return {
            "status": "success",
            "usuario": user.username,
            "total_productos": total,
            "total_stock_bajo": total_low_stock,
            "productos": [
                {
                    "id": p.id,
                    "nombre": p.name,
                    "descripcion": p.description,
                    "cantidad_disponible": p.cantidad_disponible,
                    "cantidad_minima": p.cantidad_minima,
                    "alerta_stock_bajo": p.is_low_stock,
                }
                for p in items
            ],
        }
    except AuthenticationError as e:
        return {
            "status": "error",
            "error": "TOKEN_INVALIDO",
            "detail": str(e),
        }
    finally:
        if db_session is not None:
            db_session.close()


def consultar_productos_stock_bajo(
    token: str,
    auth_service: Optional[AuthService] = None,
    product_service: Optional[ProductService] = None,
) -> Dict[str, Any]:
    """Obtiene únicamente aquellos productos del usuario autenticado cuyas existencias son críticas o bajas."""
    res = consultar_inventario(
        token=token,
        solo_stock_bajo=True,
        auth_service=auth_service,
        product_service=product_service,
    )
    if res.get("status") != "success":
        return res

    return {
        "status": "success",
        "usuario": res["usuario"],
        "productos_criticos_count": res["total_stock_bajo"],
        "productos_criticos": [
            {
                "id": p["id"],
                "nombre": p["nombre"],
                "cantidad_disponible": p["cantidad_disponible"],
                "cantidad_minima": p["cantidad_minima"],
                "deficiencia": max(0, p["cantidad_minima"] - p["cantidad_disponible"]),
            }
            for p in res["productos"]
        ],
    }
