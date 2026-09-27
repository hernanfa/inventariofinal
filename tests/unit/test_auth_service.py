"""Pruebas unitarias para AuthService utilizando FakeUserRepository (sin unittest.mock)."""

import pytest
from src.schemas.auth import UserRegisterRequest
from src.services.auth_service import AuthService
from src.services.exceptions import AuthenticationError, DuplicateEntityError
from tests.fakes.fake_user_repository import FakeUserRepository


def test_register_user_success(auth_service: AuthService) -> None:
    """Verifica que un usuario se registre correctamente con contraseña hasheada."""
    request = UserRegisterRequest(
        username="alice",
        email="alice@example.com",
        password="Password123!",
    )
    user = auth_service.register_user(request)

    assert user.id is not None
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.hashed_password != "Password123!"


def test_register_user_duplicate_username(auth_service: AuthService) -> None:
    """Verifica que no se permita registrar dos usuarios con el mismo username."""
    request1 = UserRegisterRequest(
        username="alice", email="alice1@example.com", password="Password123!"
    )
    auth_service.register_user(request1)

    request2 = UserRegisterRequest(
        username="alice", email="alice2@example.com", password="Password123!"
    )
    with pytest.raises(DuplicateEntityError) as exc_info:
        auth_service.register_user(request2)
    assert "nombre de usuario" in str(exc_info.value).lower()


def test_register_user_duplicate_email(auth_service: AuthService) -> None:
    """Verifica que no se permita registrar dos usuarios con el mismo email."""
    request1 = UserRegisterRequest(
        username="user1", email="shared@example.com", password="Password123!"
    )
    auth_service.register_user(request1)

    request2 = UserRegisterRequest(
        username="user2", email="shared@example.com", password="Password123!"
    )
    with pytest.raises(DuplicateEntityError) as exc_info:
        auth_service.register_user(request2)
    assert "correo" in str(exc_info.value).lower()


def test_authenticate_user_success(auth_service: AuthService) -> None:
    """Verifica que credenciales válidas generen un token JWT de acceso."""
    request = UserRegisterRequest(
        username="bob", email="bob@example.com", password="SecretPassword123!"
    )
    auth_service.register_user(request)

    token_response = auth_service.authenticate_user(username="bob", password="SecretPassword123!")
    assert token_response.access_token is not None
    assert token_response.token_type == "bearer"
    assert token_response.expires_in > 0


def test_authenticate_user_wrong_password(auth_service: AuthService) -> None:
    """Verifica que una contraseña incorrecta lance AuthenticationError."""
    request = UserRegisterRequest(
        username="bob", email="bob@example.com", password="SecretPassword123!"
    )
    auth_service.register_user(request)

    with pytest.raises(AuthenticationError):
        auth_service.authenticate_user(username="bob", password="WrongPassword!")


def test_authenticate_user_nonexistent(auth_service: AuthService) -> None:
    """Verifica que un usuario inexistente lance AuthenticationError."""
    with pytest.raises(AuthenticationError):
        auth_service.authenticate_user(username="nonexistent", password="AnyPassword123!")


def test_get_user_from_token(auth_service: AuthService) -> None:
    """Verifica la decodificación del token y obtención del usuario autenticado."""
    request = UserRegisterRequest(
        username="carol", email="carol@example.com", password="CarolPassword123!"
    )
    user = auth_service.register_user(request)
    token_response = auth_service.authenticate_user(username="carol", password="CarolPassword123!")

    current_user = auth_service.get_user_from_token(token_response.access_token)
    assert current_user.id == user.id
    assert current_user.username == "carol"


def test_get_user_from_invalid_token(auth_service: AuthService) -> None:
    """Verifica que un token inválido lance AuthenticationError."""
    with pytest.raises(AuthenticationError):
        auth_service.get_user_from_token("token.invalido.falso")


def test_password_longer_than_72_bytes_rejected(auth_service: AuthService) -> None:
    """Verifica que contraseñas mayores a 72 bytes sean rechazadas y no truncadas silenciosamente."""
    from pydantic import ValidationError
    from src.utils.security import hash_password, verify_password

    long_password = "A" * 73
    # 1. Pydantic schema validation rejects > 72 bytes
    with pytest.raises(ValidationError):
        UserRegisterRequest(username="longpw", email="longpw@example.com", password=long_password)

    # 2. Direct hash_password rejects > 72 bytes
    with pytest.raises(ValueError) as exc_info:
        hash_password(long_password)
    assert "no puede exceder los 72 bytes" in str(exc_info.value).lower()

    # 3. Direct verify_password returns False for candidate > 72 bytes without truncating
    valid_hash = hash_password("ValidPassword123!")
    assert verify_password(long_password, valid_hash) is False


def test_authenticate_password_no_silent_truncation(auth_service: AuthService) -> None:
    """Verifica que una contraseña no sea truncada silenciosamente al autenticar.
    
    Si una contraseña de 72 bytes está registrada, una variación que agregue caracteres
    después del byte 72 no debe coincidir ni autenticarse.
    """
    exact_72_pw = "P" * 72
    request = UserRegisterRequest(
        username="boundary_user", email="boundary@example.com", password=exact_72_pw
    )
    auth_service.register_user(request)

    # Autenticación con la contraseña exacta de 72 bytes es exitosa
    token_resp = auth_service.authenticate_user(username="boundary_user", password=exact_72_pw)
    assert token_resp.access_token is not None

    # Autenticación con caracteres adicionales (73 bytes) debe fallar y no hacer match por prefijo truncado
    with pytest.raises(AuthenticationError):
        auth_service.authenticate_user(username="boundary_user", password=exact_72_pw + "X")

