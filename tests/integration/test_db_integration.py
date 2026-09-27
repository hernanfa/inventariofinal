"""Prueba de integración con base de datos SQLite real (Principio VII de la Constitución)."""

import os
import tempfile
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.product import Product
from src.models.user import User
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository


@pytest.fixture
def real_sqlite_session():
    """Crea una base de datos SQLite real en archivo temporal con llaves foráneas habilitadas."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "real_test.db")
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        if os.path.exists(db_path):
            os.remove(db_path)
        os.rmdir(temp_dir)


def test_real_sqlite_persistence_and_relationships(real_sqlite_session) -> None:
    """Verifica persistencia real, llaves foráneas y unicidad en SQLite."""
    user_repo = UserRepository(real_sqlite_session)
    product_repo = ProductRepository(real_sqlite_session)

    # 1. Persistir usuario real
    user = User(
        username="real_user",
        email="real@example.com",
        hashed_password="hashed_real_password_123",
    )
    saved_user = user_repo.create(user)
    assert saved_user.id is not None

    # 2. Persistir producto asociado
    product = Product(
        user_id=saved_user.id,
        name="Taladro Percutor",
        description="Herramienta eléctrica",
        cantidad_disponible=2,
        cantidad_minima=1,
    )
    saved_product = product_repo.create(product)
    assert saved_product.id is not None
    assert saved_product.user_id == saved_user.id

    # 3. Consulta y recálculo de propiedad de dominio
    queried = product_repo.get_by_id(saved_product.id)
    assert queried is not None
    assert queried.name == "Taladro Percutor"
    assert queried.is_low_stock is False

    # 4. Modificar a stock crítico y actualizar en BD real
    queried.cantidad_disponible = 1
    product_repo.update(queried)

    updated_queried = product_repo.get_by_id(saved_product.id)
    assert updated_queried.cantidad_disponible == 1
    assert updated_queried.is_low_stock is True

    # 5. Verificar restricción de unicidad (user_id, name) a nivel de motor de BD
    duplicate_product = Product(
        user_id=saved_user.id,
        name="Taladro Percutor",
        cantidad_disponible=5,
        cantidad_minima=2,
    )
    with pytest.raises(IntegrityError):
        real_sqlite_session.add(duplicate_product)
        real_sqlite_session.commit()
    real_sqlite_session.rollback()

    # 6. Eliminación de producto en BD real
    product_repo.delete(updated_queried)
    assert product_repo.get_by_id(saved_product.id) is None
