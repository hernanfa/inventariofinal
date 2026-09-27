"""Inyección de dependencias para routers de FastAPI (Sesión, Servicios y Autenticación)."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.models.base import get_db
from src.models.user import User
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService
from src.services.exceptions import AuthenticationError
from src.services.product_service import ProductService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Provee una instancia de UserRepository conectada a la sesión de BD."""
    return UserRepository(db)


def get_product_repository(db: Session = Depends(get_db)) -> ProductRepository:
    """Provee una instancia de ProductRepository conectada a la sesión de BD."""
    return ProductRepository(db)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> AuthService:
    """Provee una instancia de AuthService con repositorio inyectado."""
    return AuthService(user_repository=user_repo)


def get_product_service(
    product_repo: ProductRepository = Depends(get_product_repository),
) -> ProductService:
    """Provee una instancia de ProductService con repositorio inyectado."""
    return ProductService(product_repository=product_repo)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Extrae y valida el usuario actual a partir de la cabecera Authorization Bearer."""
    try:
        return auth_service.get_user_from_token(token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
