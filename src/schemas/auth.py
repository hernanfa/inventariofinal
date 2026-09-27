"""Esquemas Pydantic para registro, autenticación y respuesta de usuarios."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    """Esquema de solicitud para registrar una nueva cuenta de usuario."""

    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario alfanumérico único")
    email: EmailStr = Field(..., description="Correo electrónico válido")
    password: str = Field(..., min_length=8, description="Contraseña de al menos 8 caracteres (máximo 72 bytes)")

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede exceder 72 bytes para evitar truncamiento silencioso")
        return v


class UserLoginRequest(BaseModel):
    """Esquema de solicitud para inicio de sesión."""

    username: str = Field(..., description="Nombre de usuario registrado")
    password: str = Field(..., description="Contraseña del usuario")


class TokenResponse(BaseModel):
    """Esquema de respuesta con token JWT de acceso."""

    access_token: str = Field(..., description="Token JWT firmado")
    token_type: str = Field(default="bearer", description="Tipo de token (bearer)")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")


class UserResponse(BaseModel):
    """Esquema de respuesta con datos públicos del usuario autenticado."""

    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
