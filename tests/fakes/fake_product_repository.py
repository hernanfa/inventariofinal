"""Repositorio falso de productos en memoria para pruebas unitarias sin mocks."""

from typing import Dict, List, Optional
from src.models.product import Product


class FakeProductRepository:
    """Implementación en memoria de ProductRepositoryProtocol."""

    def __init__(self) -> None:
        self.products: Dict[int, Product] = {}
        self._next_id: int = 1

    def get_by_id(self, product_id: int) -> Optional[Product]:
        return self.products.get(product_id)

    def get_by_user_and_id(self, user_id: int, product_id: int) -> Optional[Product]:
        product = self.products.get(product_id)
        if product and product.user_id == user_id:
            return product
        return None

    def get_by_user_and_name(self, user_id: int, name: str) -> Optional[Product]:
        normalized_name = name.strip().lower()
        for product in self.products.values():
            if product.user_id == user_id and product.name.strip().lower() == normalized_name:
                return product
        return None

    def _filter_products(
        self,
        user_id: int,
        solo_stock_bajo: bool = False,
        busqueda: Optional[str] = None,
    ) -> List[Product]:
        filtered: List[Product] = []
        for product in self.products.values():
            if product.user_id != user_id:
                continue
            if solo_stock_bajo and not (product.cantidad_disponible <= product.cantidad_minima):
                continue
            if busqueda:
                term = busqueda.strip().lower()
                desc = (product.description or "").lower()
                if term not in product.name.lower() and term not in desc:
                    continue
            filtered.append(product)
        return filtered

    def list_by_user(
        self,
        user_id: int,
        solo_stock_bajo: bool = False,
        busqueda: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Product]:
        filtered = self._filter_products(user_id, solo_stock_bajo, busqueda)
        # Ordenar por id ascendente
        filtered.sort(key=lambda p: p.id)
        return filtered[skip : skip + limit]

    def count_by_user(
        self,
        user_id: int,
        solo_stock_bajo: bool = False,
        busqueda: Optional[str] = None,
    ) -> int:
        return len(self._filter_products(user_id, solo_stock_bajo, busqueda))

    def create(self, product: Product) -> Product:
        if getattr(product, "id", None) is None or product.id == 0:
            product.id = self._next_id
            self._next_id += 1
        self.products[product.id] = product
        return product

    def update(self, product: Product) -> Product:
        self.products[product.id] = product
        return product

    def delete(self, product: Product) -> None:
        if product.id in self.products:
            del self.products[product.id]
