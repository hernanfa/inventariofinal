"""Pruebas unitarias para alertas de stock crítico y bajo (cantidad_disponible <= cantidad_minima)."""

from src.schemas.product import ProductCreateRequest
from src.services.product_service import ProductService


def test_is_low_stock_evaluation(product_service: ProductService) -> None:
    """Verifica que la propiedad is_low_stock sea True cuando disponible <= minima y False en caso contrario."""
    # 1. Stock holgado: disponible > minima
    p_ok = product_service.create_product(
        user_id=1,
        request=ProductCreateRequest(name="Producto Normal", cantidad_disponible=10, cantidad_minima=2),
    )
    assert p_ok.is_low_stock is False

    # 2. Umbral exacto alcanzado: disponible == minima
    p_threshold = product_service.create_product(
        user_id=1,
        request=ProductCreateRequest(name="Producto Umbral", cantidad_disponible=3, cantidad_minima=3),
    )
    assert p_threshold.is_low_stock is True

    # 3. Déficit de existencias: disponible < minima
    p_deficit = product_service.create_product(
        user_id=1,
        request=ProductCreateRequest(name="Producto Deficit", cantidad_disponible=1, cantidad_minima=5),
    )
    assert p_deficit.is_low_stock is True


def test_filter_low_stock_products(product_service: ProductService) -> None:
    """Verifica que el filtrado por solo_stock_bajo devuelva únicamente productos en condición crítica."""
    product_service.create_product(
        user_id=1, request=ProductCreateRequest(name="Normal 1", cantidad_disponible=20, cantidad_minima=5)
    )
    product_service.create_product(
        user_id=1, request=ProductCreateRequest(name="Critico Igual", cantidad_disponible=4, cantidad_minima=4)
    )
    product_service.create_product(
        user_id=1, request=ProductCreateRequest(name="Critico Menor", cantidad_disponible=2, cantidad_minima=8)
    )

    # Consulta con solo_stock_bajo=True
    items, total, total_low_stock = product_service.list_products(user_id=1, solo_stock_bajo=True)

    assert total == 3
    assert total_low_stock == 2
    assert len(items) == 2
    nombres_criticos = [p.name for p in items]
    assert "Critico Igual" in nombres_criticos
    assert "Critico Menor" in nombres_criticos
    assert "Normal 1" not in nombres_criticos
