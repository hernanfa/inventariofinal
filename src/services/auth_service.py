"""Servicio de autenticación y gestión de usuarios."""

from src.config import get_settings
from src.models.user import User
from src.repositories.base import UserRepositoryProtocol
from src.schemas.auth import TokenResponse, UserRegisterRequest
from src.services.exceptions import AuthenticationError, DuplicateEntityError
from src.utils.security import create_access_token, decode_access_token, hash_password, verify_password


class AuthService:
    """Lógica de negocio para registro, autenticación y resolución de identidad de usuarios."""

    def __init__(self, user_repository: UserRepositoryProtocol) -> None:
        self.user_repository = user_repository
        self.settings = get_settings()

    def register_user(self, request: UserRegisterRequest) -> User:
        """Registra un nuevo usuario asegurando la unicidad de nombre de usuario y correo."""
        normalized_username = request.username.strip()
        normalized_email = request.email.strip().lower()

        if self.user_repository.get_by_username(normalized_username) is not None:
            raise DuplicateEntityError("El nombre de usuario ya se encuentra registrado")

        if self.user_repository.get_by_email(normalized_email) is not None:
            raise DuplicateEntityError("El correo electrónico ya se encuentra registrado")

        hashed_pw = hash_password(request.password)
        new_user = User(
            username=normalized_username,
            email=normalized_email,
            hashed_password=hashed_pw,
        )
        return self.user_repository.create(new_user)

    def authenticate_user(self, username: str, password: str) -> TokenResponse:
        """Valida credenciales de acceso y retorna un token JWT firmado."""
        user = self.user_repository.get_by_username(username.strip())
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Credenciales inválidas")

        token_data = {"sub": str(user.id), "username": user.username}
        access_token = create_access_token(token_data)
        expires_in = self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
        )

    def get_user_from_token(self, token: str) -> User:
        """Resuelve el usuario autenticado a partir de un token JWT."""
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise AuthenticationError("Token inválido o expirado")

        try:
            user_id = int(payload["sub"])
        except (ValueError, TypeError):
            raise AuthenticationError("Formato de identificador en token inválido")

        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise AuthenticationError("Usuario asociado al token no existe")

        return user
