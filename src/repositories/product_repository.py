"""Implementación de ProductRepositoryProtocol utilizando SQLAlchemy."""

from typing import List, Optional
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.models.product import Product
from src.repositories.base import ProductRepositoryProtocol


class ProductRepository:
    """Repositorio para gestionar la persistencia relacional de productos con SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, product_id: int) -> Optional[Product]:
        stmt = select(Product).where(Product.id == product_id)
        return self.db.scalars(stmt).first()

    def get_by_user_and_id(self, user_id: int, product_id: int) -> Optional[Product]:
        stmt = select(Product).where(
            Product.id == product_id,
            Product.user_id == user_id,
        )
        return self.db.scalars(stmt).first()

    def get_by_user_and_name(self, user_id: int, name: str) -> Optional[Product]:
        stmt = select(Product).where(
            Product.user_id == user_id,
            func.lower(Product.name) == name.strip().lower(),
        )
        return self.db.scalars(stmt).first()

    def _build_filter_stmt(
        self,
        user_id: int,
        solo_stock_bajo: bool = False,
        busqueda: Optional[str] = None,
    ):
        stmt = select(Product).where(Product.user_id == user_id)
        if solo_stock_bajo:
            stmt = stmt.where(Product.cantidad_disponible <= Product.cantidad_minima)
        if busqueda:
            term = f"%{busqueda.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Product.name).like(term),
                    func.lower(Product.description).like(term),
                )
            )
        return stmt

    def list_by_user(
        self,
        user_id: int,
        solo_stock_bajo: bool = False,
        busqueda: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Product]:
        stmt = self._build_filter_stmt(user_id, solo_stock_bajo, busqueda)
        stmt = stmt.order_by(Product.id.asc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count_by_user(
        self,
        user_id: int,
        solo_stock_bajo: bool = False,
        busqueda: Optional[str] = None,
    ) -> int:
        stmt = select(func.count(Product.id)).where(Product.user_id == user_id)
        if solo_stock_bajo:
            stmt = stmt.where(Product.cantidad_disponible <= Product.cantidad_minima)
        if busqueda:
            term = f"%{busqueda.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Product.name).like(term),
                    func.lower(Product.description).like(term),
                )
            )
        return self.db.scalar(stmt) or 0

    def create(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def delete(self, product: Product) -> None:
        self.db.delete(product)
        self.db.commit()
