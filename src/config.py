"""Módulo de configuración centralizada con Pydantic Settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración del sistema cargada desde variables de entorno o archivo .env."""

    DATABASE_URL: str = "sqlite:///./inventario.db"
    SECRET_KEY: str = "clave_secreta_super_segura_para_jwt_inventario_personal_12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Retorna una instancia única en caché de la configuración del sistema."""
    return Settings()
