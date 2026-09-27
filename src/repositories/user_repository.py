"""Implementación de UserRepositoryProtocol utilizando SQLAlchemy."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.user import User
from src.repositories.base import UserRepositoryProtocol


class UserRepository:
    """Repositorio para gestionar la persistencia de usuarios en base de datos relacional."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        return self.db.scalars(stmt).first()

    def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        return self.db.scalars(stmt).first()

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return self.db.scalars(stmt).first()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
