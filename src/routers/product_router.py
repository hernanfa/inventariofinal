"""Router para gestión de productos e inventario personal."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.models.user import User
from src.routers.dependencies import get_current_user, get_product_service
from src.schemas.product import (
    ProductAdjustStockRequest,
    ProductCreateRequest,
    ProductListResponse,
    ProductResponse,
    ProductUpdateRequest,
)
from src.services.exceptions import (
    ConfirmationRequiredError,
    DuplicateEntityError,
    InvariantViolationError,
    ProductNotFoundError,
)
from src.services.product_service import ProductService

router = APIRouter(prefix="/api/v1/products", tags=["Productos"])


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo producto en el inventario personal",
)
def create_product(
    request: ProductCreateRequest,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Crea un nuevo producto en el catálogo personal del usuario autenticado."""
    try:
        product = product_service.create_product(user_id=current_user.id, request=request)
        return ProductResponse.model_validate(product)
    except DuplicateEntityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvariantViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=ProductListResponse,
    summary="Listar productos del usuario autenticado con filtros",
)
def list_products(
    low_stock: Optional[bool] = Query(default=False, description="Filtrar solo productos con stock bajo o crítico"),
    search: Optional[str] = Query(default=None, description="Búsqueda por nombre o descripción"),
    skip: int = Query(default=0, ge=0, description="Cantidad de registros a omitir para paginación"),
    limit: int = Query(default=50, ge=1, le=100, description="Límite de registros por página"),
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductListResponse:
    """Retorna los productos del usuario con paginación y filtros de stock bajo o término de búsqueda."""
    items, total, total_low_stock = product_service.list_products(
        user_id=current_user.id,
        solo_stock_bajo=bool(low_stock),
        busqueda=search,
        skip=skip,
        limit=limit,
    )
    return ProductListResponse(
        items=[ProductResponse.model_validate(p) for p in items],
        total=total,
        total_low_stock=total_low_stock,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Obtener detalle de un producto propio",
)
def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Obtiene un producto verificando que pertenezca al usuario autenticado (anti-BOLA)."""
    try:
        product = product_service.get_product(user_id=current_user.id, product_id=product_id)
        return ProductResponse.model_validate(product)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Actualizar atributos de un producto propio",
)
def update_product(
    product_id: int,
    request: ProductUpdateRequest,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Actualiza datos de un producto revalidando no negatividad de cantidades y unicidad de nombre."""
    try:
        product = product_service.update_product(
            user_id=current_user.id, product_id=product_id, request=request
        )
        return ProductResponse.model_validate(product)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicateEntityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvariantViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un producto propio del inventario",
)
def delete_product(
    product_id: int,
    confirm: bool = Query(
        False,
        description="Confirmación explícita requerida por el servidor para eliminar el producto",
    ),
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
) -> None:
    """Elimina definitivamente un producto perteneciente al usuario autenticado tras confirmación explícita."""
    try:
        product_service.delete_product(
            user_id=current_user.id, product_id=product_id, confirm=confirm
        )
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConfirmationRequiredError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{product_id}/adjust-stock",
    response_model=ProductResponse,
    summary="Ajustar existencias de un producto propio",
)
def adjust_stock(
    product_id: int,
    request: ProductAdjustStockRequest,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Ajusta las existencias disponibles de un producto validando que no sea negativo."""
    try:
        product = product_service.adjust_stock(
            user_id=current_user.id,
            product_id=product_id,
            nueva_cantidad_disponible=request.nueva_cantidad_disponible,
        )
        return ProductResponse.model_validate(product)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvariantViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
