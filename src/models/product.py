"""Modelo ORM Product para la tabla 'products'."""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.user import User


class Product(Base):
    """Entidad Product que representa un artículo dentro del inventario personal de un usuario."""

    __tablename__ = "products"

    __table_args__ = (
        CheckConstraint("cantidad_disponible >= 0", name="ck_cantidad_disponible_non_negative"),
        CheckConstraint("cantidad_minima >= 0", name="ck_cantidad_minima_non_negative"),
        UniqueConstraint("user_id", "name", name="uq_user_product_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cantidad_disponible: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cantidad_minima: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relación N a 1 con el usuario propietario
    owner: Mapped["User"] = relationship("User", back_populates="products")

    @property
    def is_low_stock(self) -> bool:
        """Indica si el producto tiene stock crítico (cantidad_disponible <= cantidad_minima)."""
        return self.cantidad_disponible <= self.cantidad_minima

    def __repr__(self) -> str:
        return (
            f"<Product id={self.id} user_id={self.user_id} name='{self.name}' "
            f"disponible={self.cantidad_disponible} minima={self.cantidad_minima}>"
        )
