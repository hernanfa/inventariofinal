"""Repositorio falso de usuarios en memoria para pruebas unitarias sin mocks."""

from typing import Dict, Optional
from src.models.user import User


class FakeUserRepository:
    """Implementación en memoria de UserRepositoryProtocol sin base de datos real."""

    def __init__(self) -> None:
        self.users: Dict[int, User] = {}
        self._next_id: int = 1

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.users.get(user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        for user in self.users.values():
            if user.username.lower() == username.lower():
                return user
        return None

    def get_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email.lower() == email.lower():
                return user
        return None

    def create(self, user: User) -> User:
        if getattr(user, "id", None) is None or user.id == 0:
            user.id = self._next_id
            self._next_id += 1
        self.users[user.id] = user
        return user
