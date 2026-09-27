"""Fixtures globales para la suite de pruebas pytest."""

import pytest
from tests.fakes.fake_user_repository import FakeUserRepository
from tests.fakes.fake_product_repository import FakeProductRepository
from src.services.auth_service import AuthService
from src.services.product_service import ProductService


@pytest.fixture
def fake_user_repo() -> FakeUserRepository:
    """Provee una instancia limpia de FakeUserRepository en memoria."""
    return FakeUserRepository()


@pytest.fixture
def fake_product_repo() -> FakeProductRepository:
    """Provee una instancia limpia de FakeProductRepository en memoria."""
    return FakeProductRepository()


@pytest.fixture
def auth_service(fake_user_repo: FakeUserRepository) -> AuthService:
    """Provee una instancia de AuthService con repositorio falso inyectado."""
    return AuthService(user_repository=fake_user_repo)


@pytest.fixture
def product_service(fake_product_repo: FakeProductRepository) -> ProductService:
    """Provee una instancia de ProductService con repositorio falso inyectado."""
    return ProductService(product_repository=fake_product_repo)
