"""Punto de entrada principal de la aplicación FastAPI."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.models.base import Base, engine
from src.routers.auth_router import router as auth_router
from src.routers.product_router import router as product_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación: crea tablas de base de datos al inicio."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Inventario Personal API",
    description="API REST para gestión segura y aislada de inventario personal con MCP.",
    version="2.0.0",
    lifespan=lifespan,
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de routers por capa
app.include_router(auth_router)
app.include_router(product_router)


@app.get("/health", tags=["Salud"])
def health_check():
    """Endpoint de verificación de estado y salud del servicio."""
    return {"status": "ok", "version": "2.0.0"}
