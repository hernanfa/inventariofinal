"""Esquemas Pydantic para creación, edición, ajuste y listado de productos."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductCreateRequest(BaseModel):
    """Esquema de solicitud para registrar un nuevo producto en el inventario."""

    name: str = Field(..., min_length=1, max_length=100, description="Nombre del producto")
    description: Optional[str] = Field(default=None, max_length=500, description="Descripción opcional")
    cantidad_disponible: int = Field(default=0, description="Cantidad en existencia (entero >= 0)")
    cantidad_minima: int = Field(default=0, description="Cantidad mínima de seguridad (entero >= 0)")


class ProductUpdateRequest(BaseModel):
    """Esquema de solicitud para actualizar campos de un producto existente."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Nuevo nombre del producto")
    description: Optional[str] = Field(default=None, max_length=500, description="Nueva descripción opcional")
    cantidad_disponible: Optional[int] = Field(default=None, description="Nueva cantidad disponible (>= 0)")
    cantidad_minima: Optional[int] = Field(default=None, description="Nueva cantidad mínima (>= 0)")


class ProductAdjustStockRequest(BaseModel):
    """Esquema para ajustar la cantidad disponible de un producto."""

    nueva_cantidad_disponible: int = Field(
        ..., description="Nueva cantidad disponible absoluta (entero >= 0)"
    )
    motivo: Optional[str] = Field(default=None, max_length=200, description="Motivo del ajuste")


class ProductResponse(BaseModel):
    """Esquema de respuesta detallada de un producto de inventario."""

    id: int
    user_id: int
    name: str
    description: Optional[str]
    cantidad_disponible: int
    cantidad_minima: int
    is_low_stock: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Esquema de respuesta paginada con resumen de catálogo de productos."""

    items: List[ProductResponse]
    total: int
    total_low_stock: int
