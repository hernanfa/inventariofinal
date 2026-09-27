"""Router de autenticación para registro, inicio de sesión y consulta de perfil."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.models.user import User
from src.routers.dependencies import get_auth_service, get_current_user
from src.schemas.auth import TokenResponse, UserRegisterRequest, UserResponse
from src.services.auth_service import AuthService
from src.services.exceptions import AuthenticationError, DuplicateEntityError

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva cuenta de usuario",
)
def register(
    request: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Crea una nueva cuenta de usuario con contraseña hasheada y aislamiento garantizado."""
    try:
        return auth_service.register_user(request)
    except (DuplicateEntityError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión y obtener token JWT de acceso",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Valida credenciales de acceso vía formulario OAuth2 y emite un token JWT de acceso."""
    try:
        return auth_service.authenticate_user(
            username=form_data.username,
            password=form_data.password,
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener perfil del usuario autenticado",
)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Retorna los datos del usuario actualmente autenticado."""
    return current_user
