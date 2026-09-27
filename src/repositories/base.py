"""Protocolos e interfaces tipadas para la capa de repositorios."""

from typing import List, Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.product import Product


class UserRepositoryProtocol(Protocol):
    """Protocolo que define las operaciones de acceso a datos para usuarios."""

    def get_by_id(self, user_id: int) -> Optional["User"]:
        ...

    def get_by_username(self, username: str) -> Optional["User"]:
        ...

    def get_by_email(self, email: str) -> Optional["User"]:
        ...

    def create(self, user: "User") -> "User":
        ...


class ProductRepositoryProtocol(Protocol):
    """Protocolo que define las operaciones de acceso a datos para productos."""

    def get_by_id(self, product_id: int) -> Optional["Product"]:
        ...

    def get_by_user_and_id(self, user_id: int, product_id: int) -> Optional["Product"]:
        ...

    def get_by_user_and_name(self, user_id: int, name: str) -> Optional["Product"]:
        ...

    def list_by_user(
        self,
        user_id: int,
        solo_stock_bajo: bool = False,
        busqueda: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List["Product"]:
        ...

    def count_by_user(
        self,
        user_id: int,
        solo_stock_bajo: bool = False,
        busqueda: Optional[str] = None,
    ) -> int:
        ...

    def create(self, product: "Product") -> "Product":
        ...

    def update(self, product: "Product") -> "Product":
        ...

    def delete(self, product: "Product") -> None:
        ...
