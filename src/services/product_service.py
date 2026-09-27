"""Servicio de dominio para la gestión del inventario personal de productos."""

from typing import List, Optional, Tuple
from src.models.product import Product
from src.repositories.base import ProductRepositoryProtocol
from src.schemas.product import ProductCreateRequest, ProductUpdateRequest
from src.services.exceptions import (
    ConfirmationRequiredError,
    DuplicateEntityError,
    InvariantViolationError,
    ProductNotFoundError,
)


class ProductService:
    """Lógica de negocio y reglas de dominio para productos con aislamiento por usuario."""

    def __init__(self, product_repository: ProductRepositoryProtocol) -> None:
        self.product_repository = product_repository

    def create_product(self, user_id: int, request: ProductCreateRequest) -> Product:
        """Crea un nuevo producto garantizando cantidades no negativas y unicidad de nombre por usuario."""
        if request.cantidad_disponible < 0 or request.cantidad_minima < 0:
            raise InvariantViolationError("Las cantidades deben ser números enteros mayores o iguales a cero")

        clean_name = request.name.strip()
        if not clean_name:
            raise InvariantViolationError("El nombre del producto no puede estar vacío")

        # Verificar unicidad dentro del catálogo del mismo usuario
        existing = self.product_repository.get_by_user_and_name(user_id, clean_name)
        if existing is not None:
            raise DuplicateEntityError(
                f"Ya existe un producto con el nombre '{clean_name}' en tu inventario"
            )

        product = Product(
            user_id=user_id,
            name=clean_name,
            description=request.description.strip() if request.description else None,
            cantidad_disponible=request.cantidad_disponible,
            cantidad_minima=request.cantidad_minima,
        )
        return self.product_repository.create(product)

    def get_product(self, user_id: int, product_id: int) -> Product:
        """Obtiene un producto verificando estrictamente la pertenencia al usuario (defensa anti-BOLA)."""
        product = self.product_repository.get_by_user_and_id(user_id, product_id)
        if product is None:
            raise ProductNotFoundError("Producto no encontrado")
        return product

    def list_products(
        self,
        user_id: int,
        solo_stock_bajo: bool = False,
        busqueda: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Product], int, int]:
        """Retorna productos paginados, total general y total con stock bajo pertenecientes al usuario."""
        items = self.product_repository.list_by_user(
            user_id=user_id,
            solo_stock_bajo=solo_stock_bajo,
            busqueda=busqueda,
            skip=skip,
            limit=limit,
        )
        total = self.product_repository.count_by_user(
            user_id=user_id,
            busqueda=busqueda,
        )
        total_low_stock = self.product_repository.count_by_user(
            user_id=user_id,
            solo_stock_bajo=True,
            busqueda=busqueda,
        )
        return items, total, total_low_stock

    def update_product(
        self, user_id: int, product_id: int, request: ProductUpdateRequest
    ) -> Product:
        """Actualiza atributos de un producto propio revalidando cantidades y unicidad de nombre."""
        product = self.get_product(user_id, product_id)

        if request.name is not None:
            clean_name = request.name.strip()
            if not clean_name:
                raise InvariantViolationError("El nombre del producto no puede estar vacío")
            if clean_name.lower() != product.name.lower():
                existing = self.product_repository.get_by_user_and_name(user_id, clean_name)
                if existing is not None:
                    raise DuplicateEntityError(
                        f"Ya existe un producto con el nombre '{clean_name}' en tu inventario"
                    )
            product.name = clean_name

        if request.description is not None:
            product.description = request.description.strip() if request.description else None

        if request.cantidad_disponible is not None:
            if request.cantidad_disponible < 0:
                raise InvariantViolationError("La cantidad disponible no puede ser negativa")
            product.cantidad_disponible = request.cantidad_disponible

        if request.cantidad_minima is not None:
            if request.cantidad_minima < 0:
                raise InvariantViolationError("La cantidad mínima no puede ser negativa")
            product.cantidad_minima = request.cantidad_minima

        # Revalidación de invariante de no negatividad en ambas cantidades
        if product.cantidad_disponible < 0 or product.cantidad_minima < 0:
            raise InvariantViolationError("Las cantidades deben ser enteros no negativos")

        return self.product_repository.update(product)

    def delete_product(
        self, user_id: int, product_id: int, confirm: bool = False
    ) -> None:
        """Elimina un producto asegurando la propiedad del usuario y confirmación explícita (FR-012)."""
        product = self.get_product(user_id, product_id)
        if not confirm:
            raise ConfirmationRequiredError(
                "Se requiere confirmación explícita para eliminar el producto"
            )
        self.product_repository.delete(product)

    def adjust_stock(
        self, user_id: int, product_id: int, nueva_cantidad_disponible: int
    ) -> Product:
        """Ajusta las existencias disponibles de un producto validando que no sea negativo."""
        if nueva_cantidad_disponible < 0:
            raise InvariantViolationError("La cantidad disponible no puede ser negativa")

        product = self.get_product(user_id, product_id)
        product.cantidad_disponible = nueva_cantidad_disponible
        return self.product_repository.update(product)
