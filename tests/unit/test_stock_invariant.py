"""Pruebas unitarias para la regla de stock no negativo y ajustes de existencias."""

import pytest
from src.schemas.product import ProductCreateRequest, ProductUpdateRequest
from src.services.exceptions import InvariantViolationError
from src.services.product_service import ProductService


def test_adjust_stock_to_deficit_allowed(product_service: ProductService) -> None:
    """Verifica que ajustar stock por debajo del mínimo sea permitido y active is_low_stock."""
    p = product_service.create_product(
        user_id=1,
        request=ProductCreateRequest(name="Azúcar", cantidad_disponible=10, cantidad_minima=5),
    )
    assert p.is_low_stock is False

    # Reducción por debajo de la mínima: 2 < 5
    adjusted = product_service.adjust_stock(user_id=1, product_id=p.id, nueva_cantidad_disponible=2)
    assert adjusted.cantidad_disponible == 2
    assert adjusted.cantidad_minima == 5
    assert adjusted.is_low_stock is True


def test_adjust_stock_negative_rejected(product_service: ProductService) -> None:
    """Verifica que intentar ajustar a una cantidad negativa sea rechazado con InvariantViolationError."""
    p = product_service.create_product(
        user_id=1,
        request=ProductCreateRequest(name="Sal", cantidad_disponible=5, cantidad_minima=2),
    )

    with pytest.raises(InvariantViolationError) as exc_info:
        product_service.adjust_stock(user_id=1, product_id=p.id, nueva_cantidad_disponible=-1)
    assert "no puede ser negativa" in str(exc_info.value).lower()


def test_create_product_negative_quantities_rejected(product_service: ProductService) -> None:
    """Verifica que crear productos con cantidades negativas sea rechazado."""
    with pytest.raises(InvariantViolationError):
        product_service.create_product(
            user_id=1,
            request=ProductCreateRequest(name="Inv1", cantidad_disponible=-5, cantidad_minima=2),
        )

    with pytest.raises(InvariantViolationError):
        product_service.create_product(
            user_id=1,
            request=ProductCreateRequest(name="Inv2", cantidad_disponible=5, cantidad_minima=-2),
        )


def test_update_product_negative_quantities_rejected(product_service: ProductService) -> None:
    """Verifica que actualizar productos a cantidades negativas sea rechazado."""
    p = product_service.create_product(
        user_id=1,
        request=ProductCreateRequest(name="Válido", cantidad_disponible=5, cantidad_minima=2),
    )

    with pytest.raises(InvariantViolationError):
        product_service.update_product(
            user_id=1,
            product_id=p.id,
            request=ProductUpdateRequest(cantidad_disponible=-3),
        )

    with pytest.raises(InvariantViolationError):
        product_service.update_product(
            user_id=1,
            product_id=p.id,
            request=ProductUpdateRequest(cantidad_minima=-1),
        )
