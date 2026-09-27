# Implementation Plan: Inventario Personal

**Branch**: `001-personal-inventory` | **Date**: 2026-09-25 | **Spec**: [specs/001-personal-inventory/spec.md](file:///D:/PracticasCursos/PIntegrador/inventariofinal/specs/001-personal-inventory/spec.md)

**Input**: Feature specification from `specs/001-personal-inventory/spec.md`

## Summary

Desarrollo de la aplicación web y servidor MCP de **Inventario Personal** con arquitectura por capas estricta en Python. El sistema permite el registro y autenticación de usuarios mediante OAuth2/JWT, la administración aislada y exclusiva de productos (CRUD), la identificación y alerta de existencias críticas (`cantidad_disponible <= cantidad_minima`), la validación rigurosa de cantidades no negativas (`cantidad_disponible >= 0`, `cantidad_minima >= 0`) permitiendo que la cantidad disponible sea menor a la mínima para reflejar el consumo real y activar alertas, y la exposición de herramientas MCP que reutilizan la lógica de negocio validando la identidad del usuario. La persistencia se basa en SQLite con SQLAlchemy mediante repositorios inyectados, y las pruebas se implementan con pytest utilizando repositorios falsos en memoria (sin `unittest.mock`) y al menos una prueba con base de datos real, alcanzando coberturas mínimas de 90 % en `services` y 70 % global.

---

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI (0.110+), Pydantic v2, SQLAlchemy 2.0, PyJWT, passlib[bcrypt], uvicorn, fastmcp / mcp  
**Storage**: SQLite (`sqlite:///./inventario.db`) gestionado mediante SQLAlchemy con llaves foráneas activadas y restricciones de unicidad (`UniqueConstraint('user_id', 'name')`)  
**Testing**: pytest, pytest-cov, fake repositories en memoria (`tests/fakes/`), y suite de integración con SQLite real  
**Target Platform**: Servidor Web / API REST local y contenedorizable  
**Project Type**: web-service (API REST con FastAPI) + servidor Model Context Protocol (MCP)  
**Performance Goals**: Respuestas HTTP < 50ms para operaciones CRUD de inventario; consultas MCP < 100ms  
**Constraints**:
- Cumplimiento de los 7 principios constitucionales del proyecto (Constitución v2.0.0).
- Invariante de no negatividad: `cantidad_disponible >= 0` y `cantidad_minima >= 0`. Se permite explícitamente `cantidad_disponible < cantidad_minima` para detectar stock crítico cuando `cantidad_disponible <= cantidad_minima`.
- Revalidación obligatoria de ambas cantidades en edición de productos (`PUT`).
- Control de nombres duplicados por usuario: captura de `UniqueConstraint` en `ProductService` y retorno controlado de HTTP 400 Bad Request (`DuplicateEntityError`) sin exponer errores internos de base de datos.
- Aislamiento total de recursos por usuario (`user_id` verificado en `services`).
- Prohibición estricta de `unittest.mock` en pruebas unitarias de `services`.
- Umbral de cobertura mínimo: >= 90 % en `services/` y >= 70 % global del proyecto.
- Secretos en `.env`, fuera del repositorio Git.  
**Scale/Scope**: Gestión de inventario personal por usuario, con cientos de ítems individuales por cuenta.

---

## Constitution Check

*GATE: Evaluado antes de diseño y re-verificado tras la definición de contratos y arquitectura.*

| Principio Constitucional | Requerimiento de la Constitución | Estado del Diseño | Evidencia en el Plan |
|---|---|---|---|
| **I. Arquitectura por Capas** | Separación estricta: `routers`, `mcp`, `services`, `repositories`, `models`, `schemas`, `utils`. No saltarse capas. | **PASS** | Estructura en `src/` modularizada. `routers` y `mcp` solo consumen `services`. |
| **II. Lógica en Services** | Reglas de negocio e invariantes en `services` con repositorios inyectados (DI). | **PASS** | Reglas de stock no negativo y unicidad gestionadas en `ProductService` con interfaz `ProductRepository`. |
| **III. Aislamiento por Usuario** | Todo producto pertenece exclusivamente a `user_id`. Prohibido acceso cruzado (BOLA/IDOR). | **PASS** | Métodos de servicio exigen `user_id`; consultas y mutaciones filtradas obligatoriamente por propietario. |
| **IV. Seguridad y Secretos** | OAuth2 + JWT, contraseñas con bcrypt y secretos cargados desde `.env` fuera de Git. | **PASS** | Módulo `utils/security.py`, `config.py` con `pydantic-settings`, `.env.example` y regla en `.gitignore`. |
| **V. Cantidades No Negativas y Alerta de Stock Mínimo** | CRUD REST completo, `disponible >= 0` y `minima >= 0`, alerta en `disponible <= minima`, y bloqueo de stock negativo (`< 0`). | **PASS** | Contratos en `contracts/rest-api.md`, validación en `ProductService` y rechazo HTTP 400 ante cantidades negativas. |
| **VI. Herramientas MCP Seguras** | Al menos 2 tools MCP que reutilicen `services` y verifiquen la identidad del usuario. | **PASS** | Tools `consultar_inventario` y `consultar_productos_stock_bajo` consumen `ProductService` con token JWT validado. |
| **VII. Pirámide de Pruebas** | Fake repos sin `unittest.mock`, al menos 1 test con BD real, cobertura >= 90 % en services y >= 70 % global. | **PASS** | `FakeProductRepository` en `tests/fakes/`, `test_db_integration.py` con SQLite, comando con `--cov-fail-under`. |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-personal-inventory/
├── plan.md              # Este plan de implementación maestro
├── research.md          # Decisiones técnicas y justificaciones arquitectónicas
├── data-model.md        # Modelado ER, entidades, esquemas Pydantic y máquina de estados
├── quickstart.md        # Guía paso a paso de ejecución, validación y testing
├── contracts/           # Contratos formales de interfaces
│   ├── rest-api.md      # Especificación completa de endpoints REST
│   └── mcp-tools.md     # Especificación de herramientas y schemas MCP
└── checklists/
    └── requirements.md  # Validación de calidad de la especificación
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── config.py                 # Variables de entorno y configuración central (Pydantic Settings)
├── main.py                   # Punto de entrada de FastAPI y registro de routers
├── models/                   # Capa de Modelos ORM (SQLAlchemy)
│   ├── __init__.py
│   ├── base.py               # Base declarativa de SQLAlchemy
│   ├── user.py               # Entidad User (tabla 'users')
│   └── product.py            # Entidad Product (tabla 'products')
├── schemas/                  # Capa de Esquemas y DTOs (Pydantic v2)
│   ├── __init__.py
│   ├── auth.py               # Schemas de registro, login y tokens
│   └── product.py            # Schemas de creación, actualización y respuesta de producto
├── repositories/             # Capa de Repositorios (Acceso a datos)
│   ├── __init__.py
│   ├── base.py               # Protocolos/Interfaces tipadas para repositorios
│   ├── user_repository.py    # Implementación SQLAlchemy para User
│   └── product_repository.py # Implementación SQLAlchemy para Product
├── services/                 # Capa de Servicios (Lógica de Dominio e Invariantes)
│   ├── __init__.py
│   ├── exceptions.py         # Excepciones de negocio (ProductNotFoundError, DuplicateEntityError, etc.)
│   ├── auth_service.py       # Registro, verificación de contraseñas y emisión de JWT
│   └── product_service.py    # CRUD, ajustes de inventario, no negatividad, unicidad y filtros
├── routers/                  # Capa de Routers (Controladores HTTP FastAPI)
│   ├── __init__.py
│   ├── dependencies.py       # Inyección de dependencias (Sesión DB, Servicios, Usuario actual)
│   ├── auth_router.py        # Endpoints /api/v1/auth
│   └── product_router.py     # Endpoints /api/v1/products
├── mcp/                      # Capa MCP (Model Context Protocol para Asistentes IA)
│   ├── __init__.py
│   ├── server.py             # Servidor FastMCP / MCP estándar
│   └── tools.py              # Definición de tools que consumen ProductService validando token
└── utils/                    # Capa de Utilidades transversales
    ├── __init__.py
    └── security.py           # Funciones de hashing bcrypt y codificación/decodificación JWT

tests/
├── __init__.py
├── conftest.py               # Configuración global de pytest y fixtures
├── fakes/                    # Repositorios Falsos en memoria (cumplen protocolos de repositories/base.py)
│   ├── __init__.py
│   ├── fake_user_repository.py
│   └── fake_product_repository.py
├── unit/                     # Pruebas Unitarias de Servicios (Aislamiento, No Negatividad, Cobertura >= 90%)
│   ├── __init__.py
│   ├── test_auth_service.py
│   ├── test_product_service.py
│   └── test_mcp_tools.py
└── integration/              # Pruebas de Integración con SQLite Real y API REST
    ├── __init__.py
    ├── test_db_integration.py
    └── test_api_endpoints.py
```

**Structure Decision**: Se adopta la opción de monoproyecto modular en Python con 7 capas estrictamente aisladas bajo `src/`, asegurando que `routers` y `mcp` deleguen el 100 % de las operaciones a `services`, y que las dependencias de persistencia se inyecten limpiamente permitiendo sustitución total por `fakes` en `tests/`.

---

## Complexity Tracking

> **Violaciones a la Constitución que requieran justificación:** Ninguna. El diseño se adapta de manera nativa y directa a los 7 principios constitucionales sin introducir complejidad injustificada ni desviaciones.
