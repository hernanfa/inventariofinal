"""Pruebas unitarias de aislamiento estricto multi-inquilino entre usuarios (anti-BOLA/IDOR)."""

import pytest
from src.schemas.product import ProductCreateRequest, ProductUpdateRequest
from src.services.exceptions import ProductNotFoundError
from src.services.product_service import ProductService


def test_complete_product_isolation_between_users(product_service: ProductService) -> None:
    """Verifica de forma exhaustiva que el Usuario B no puede leer, mutar, ajustar ni borrar productos del Usuario A."""
    user_a_id = 100
    user_b_id = 200

    # Usuario A crea su producto privado
    req = ProductCreateRequest(
        name="Laptop Personal",
        description="Equipo confidencial",
        cantidad_disponible=1,
        cantidad_minima=1,
    )
    product_a = product_service.create_product(user_id=user_a_id, request=req)

    # 1. Usuario B no puede obtener el detalle del producto de A
    with pytest.raises(ProductNotFoundError):
        product_service.get_product(user_id=user_b_id, product_id=product_a.id)

    # 2. Usuario B no puede editar el producto de A
    with pytest.raises(ProductNotFoundError):
        product_service.update_product(
            user_id=user_b_id,
            product_id=product_a.id,
            request=ProductUpdateRequest(name="Laptop Hackeada"),
        )

    # 3. Usuario B no puede ajustar las existencias del producto de A
    with pytest.raises(ProductNotFoundError):
        product_service.adjust_stock(
            user_id=user_b_id,
            product_id=product_a.id,
            nueva_cantidad_disponible=0,
        )

    # 4. Usuario B no puede eliminar el producto de A
    with pytest.raises(ProductNotFoundError):
        product_service.delete_product(user_id=user_b_id, product_id=product_a.id)

    # 5. El producto de A no aparece en el catálogo de B
    items_b, total_b, _ = product_service.list_products(user_id=user_b_id)
    assert total_b == 0
    assert product_a.id not in [p.id for p in items_b]

    # 6. El producto de A se mantiene íntegro e inalterado
    preserved = product_service.get_product(user_id=user_a_id, product_id=product_a.id)
    assert preserved.name == "Laptop Personal"
    assert preserved.cantidad_disponible == 1
