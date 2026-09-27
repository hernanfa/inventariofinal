"""Utilidades de seguridad: hashing de contraseñas y gestión de tokens JWT."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
import jwt
import passlib.handlers.bcrypt as _pb_bcrypt
from passlib.context import CryptContext

from src.config import get_settings

# Compatibilidad passlib y bcrypt >= 4.0.0 / 5.0.0:
# 1. bcrypt 4+ eliminó bcrypt.__about__, lo que genera advertencias en passlib.
if not hasattr(bcrypt, "__about__"):
    class _About:
        __version__ = getattr(bcrypt, "__version__", "5.0.0")
    bcrypt.__about__ = _About()

# 2. En bcrypt >= 4.0.0, contraseñas mayores a 72 bytes lanzan ValueError.
# El probe 'detect_wrap_bug' de passlib usa 255 bytes y falla al inicializar el backend.
# Inicializamos el backend de passlib de forma segura sin ejecutar dicho probe obsoleto.
def _safe_finalize_backend_mixin(mixin_cls, name, dryrun):
    mixin_cls._has_2a_wraparound_bug = False
    mixin_cls._fallback_ident = _pb_bcrypt.IDENT_2B
    mixin_cls._workrounds_initialized = True
    return True

_pb_bcrypt._BcryptBackend._finalize_backend_mixin = classmethod(_safe_finalize_backend_mixin)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    """Genera un hash seguro para la contraseña provista utilizando bcrypt con salt.

    Rechaza contraseñas mayores a 72 bytes en UTF-8 para evitar truncamiento
    silencioso y mantener la integridad de seguridad.
    """
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > MAX_PASSWORD_BYTES:
        raise ValueError(
            f"La contraseña no puede exceder los {MAX_PASSWORD_BYTES} bytes para evitar truncamiento silencioso"
        )
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña en texto plano coincide con el hash almacenado.

    Si la contraseña candidata excede los 72 bytes, se rechaza de forma segura (retorna False)
    sin truncarla silenciosamente ni lanzar excepciones no deseadas.
    """
    pw_bytes = plain_password.encode("utf-8")
    if len(pw_bytes) > MAX_PASSWORD_BYTES:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Crea y firma un token JWT de acceso con tiempo de expiración."""
    settings = get_settings()
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodifica y valida la firma y vigencia de un token JWT. Retorna None si es inválido."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except (jwt.PyJWTError, ValueError):
        return None
