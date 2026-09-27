"""Pruebas unitarias para ProductService con FakeProductRepository (sin unittest.mock)."""

import pytest
from src.schemas.product import ProductCreateRequest, ProductUpdateRequest
from src.services.exceptions import DuplicateEntityError, ProductNotFoundError
from src.services.product_service import ProductService


def test_create_product_success(product_service: ProductService) -> None:
    """Verifica la creación exitosa de un producto para el usuario autenticado."""
    req = ProductCreateRequest(
        name="Manzanas",
        description="Bolsa de 1kg",
        cantidad_disponible=10,
        cantidad_minima=2,
    )
    product = product_service.create_product(user_id=1, request=req)

    assert product.id is not None
    assert product.user_id == 1
    assert product.name == "Manzanas"
    assert product.cantidad_disponible == 10
    assert product.cantidad_minima == 2
    assert product.is_low_stock is False


def test_create_product_duplicate_name_same_user(product_service: ProductService) -> None:
    """Verifica que no se permita crear dos productos con el mismo nombre para el mismo usuario."""
    req1 = ProductCreateRequest(name="Café", cantidad_disponible=5, cantidad_minima=2)
    product_service.create_product(user_id=1, request=req1)

    req2 = ProductCreateRequest(name="café", cantidad_disponible=10, cantidad_minima=3)
    with pytest.raises(DuplicateEntityError) as exc_info:
        product_service.create_product(user_id=1, request=req2)
    assert "ya existe un producto" in str(exc_info.value).lower()


def test_create_product_same_name_different_users(product_service: ProductService) -> None:
    """Verifica que dos usuarios distintos puedan tener productos con el mismo nombre en sus inventarios."""
    req1 = ProductCreateRequest(name="Arroz", cantidad_disponible=5, cantidad_minima=2)
    p1 = product_service.create_product(user_id=1, request=req1)

    req2 = ProductCreateRequest(name="Arroz", cantidad_disponible=8, cantidad_minima=1)
    p2 = product_service.create_product(user_id=2, request=req2)

    assert p1.id != p2.id
    assert p1.name == p2.name
    assert p1.user_id == 1
    assert p2.user_id == 2


def test_get_product_success(product_service: ProductService) -> None:
    """Verifica la consulta exitosa de un producto propio."""
    req = ProductCreateRequest(name="Leche", cantidad_disponible=3, cantidad_minima=1)
    created = product_service.create_product(user_id=1, request=req)

    fetched = product_service.get_product(user_id=1, product_id=created.id)
    assert fetched.id == created.id
    assert fetched.name == "Leche"


def test_get_product_alien_raises_not_found(product_service: ProductService) -> None:
    """Verifica que intentar obtener un producto ajeno lance ProductNotFoundError (defensa anti-BOLA)."""
    req = ProductCreateRequest(name="Pan", cantidad_disponible=2, cantidad_minima=1)
    created = product_service.create_product(user_id=1, request=req)

    with pytest.raises(ProductNotFoundError):
        product_service.get_product(user_id=2, product_id=created.id)


def test_list_products_user_isolation(product_service: ProductService) -> None:
    """Verifica que el listado contenga única y exclusivamente los productos del usuario solicitante."""
    product_service.create_product(user_id=1, request=ProductCreateRequest(name="P1_U1"))
    product_service.create_product(user_id=1, request=ProductCreateRequest(name="P2_U1"))
    product_service.create_product(user_id=2, request=ProductCreateRequest(name="P1_U2"))

    items_u1, total_u1, _ = product_service.list_products(user_id=1)
    assert total_u1 == 2
    assert all(p.user_id == 1 for p in items_u1)

    items_u2, total_u2, _ = product_service.list_products(user_id=2)
    assert total_u2 == 1
    assert all(p.user_id == 2 for p in items_u2)


def test_update_product_success_and_revalidation(product_service: ProductService) -> None:
    """Verifica la actualización de datos y revalidación de cantidades."""
    p = product_service.create_product(
        user_id=1,
        request=ProductCreateRequest(name="Cereal", cantidad_disponible=5, cantidad_minima=2),
    )

    update_req = ProductUpdateRequest(
        name="Cereal Integral",
        description="Sin azúcar",
        cantidad_disponible=1,
        cantidad_minima=3,
    )
    updated = product_service.update_product(user_id=1, product_id=p.id, request=update_req)

    assert updated.name == "Cereal Integral"
    assert updated.description == "Sin azúcar"
    assert updated.cantidad_disponible == 1
    assert updated.cantidad_minima == 3
    assert updated.is_low_stock is True


def test_update_product_duplicate_name(product_service: ProductService) -> None:
    """Verifica que no se permita renombrar un producto al nombre de otro producto existente del mismo usuario."""
    product_service.create_product(user_id=1, request=ProductCreateRequest(name="A"))
    p2 = product_service.create_product(user_id=1, request=ProductCreateRequest(name="B"))

    with pytest.raises(DuplicateEntityError):
        product_service.update_product(
            user_id=1, product_id=p2.id, request=ProductUpdateRequest(name="A")
        )


def test_update_product_alien_raises_not_found(product_service: ProductService) -> None:
    """Verifica que editar un producto ajeno lance ProductNotFoundError."""
    p = product_service.create_product(user_id=1, request=ProductCreateRequest(name="Propio"))

    with pytest.raises(ProductNotFoundError):
        product_service.update_product(
            user_id=2, product_id=p.id, request=ProductUpdateRequest(name="Hack")
        )


def test_delete_product_success(product_service: ProductService) -> None:
    """Verifica la eliminación de un producto propio."""
    p = product_service.create_product(user_id=1, request=ProductCreateRequest(name="Borrar"))
    product_service.delete_product(user_id=1, product_id=p.id)

    with pytest.raises(ProductNotFoundError):
        product_service.get_product(user_id=1, product_id=p.id)


def test_delete_product_alien_raises_not_found(product_service: ProductService) -> None:
    """Verifica que intentar eliminar un producto ajeno lance ProductNotFoundError."""
    p = product_service.create_product(user_id=1, request=ProductCreateRequest(name="NoBorrar"))

    with pytest.raises(ProductNotFoundError):
        product_service.delete_product(user_id=2, product_id=p.id)
