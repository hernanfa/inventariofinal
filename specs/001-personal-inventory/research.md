# Research & Technical Decisions: Inventario Personal

**Feature**: `specs/001-personal-inventory`  
**Date**: 2026-09-25  
**Status**: Completed (Actualizado con Regla de No Negatividad y Detección de Stock Bajo)  

---

## 1. Decisiones Tecnológicas

### 1.1 Lenguaje y Framework Web
- **Decisión**: Python 3.11+ con **FastAPI**.
- **Rationale**:
  - FastAPI ofrece soporte nativo para validación estricta y serialización con esquemas Pydantic v2.
  - Generación automática de especificaciones OpenAPI / Swagger.
  - Sistema de inyección de dependencias modular (`Depends`) para resolver servicios y contextos de autenticación.
  - Alto rendimiento asíncrono y excelente ergonomía de desarrollo.
- **Alternativas consideradas**:
  - *Flask*: Descartado por requerir múltiples librerías externas para esquemas, async y documentación OpenAPI.
  - *Django*: Descartado por ser un framework monolítico pesado (batteries-included) innecesario para una API desacoplada por capas con SQLite y MCP.

### 1.2 Persistencia y Base de Datos
- **Decisión**: **SQLite** utilizando **SQLAlchemy 2.0** como ORM y constructor de consultas mediante el patrón Repository.
- **Rationale**:
  - SQLite es liviano, autocontenido, no requiere servicios externos y cumple a la perfección el alcance de un inventario personal.
  - SQLAlchemy 2.0 permite separar limpiamente las entidades de persistencia (`models/`) de las interfaces de acceso a datos (`repositories/`).
  - Habilita tanto pruebas unitarias con repositorios en memoria (fakes) como pruebas de integración contra SQLite real en disco o memoria.
- **Alternativas consideradas**:
  - *SQLite directo con sqlite3 estándar*: Descartado porque escribir SQL manual dificulta la portabilidad y el mantenimiento de esquemas tipados.
  - *Tortoise ORM*: Descartado para preferir la madurez, tipado y soporte estándar en el ecosistema de SQLAlchemy 2.0.

### 1.3 Autenticación, Hashing y Gestión de Secretos
- **Decisión**: **OAuth2 Password Bearer** con tokens **JWT (JSON Web Tokens)** mediante `PyJWT` / `python-jose`, y hashing de contraseñas con **`passlib[bcrypt]` / `pwd_context`**. Configuración mediante **`pydantic-settings`** leyendo variables de entorno de `.env`.
- **Rationale**:
  - Cumple estrictamente con el Principio IV de la Constitución.
  - JWT permite sesiones sin estado (stateless) que transportan la identidad verificada del usuario (`user_id` / `sub`), utilizable de forma transparente tanto en endpoints HTTP como en herramientas MCP.
  - `bcrypt` garantiza almacenamiento irreversible con salt automático contra ataques de diccionario y rainbow tables.
  - `pydantic-settings` asegura que los secretos nunca se definan en duro en el código y que el archivo `.env` sea ignorado por Git.
- **Alternativas consideradas**:
  - *Sesiones basadas en cookies*: Descartadas para facilitar la autenticación unificada entre clientes web, API REST y servidores/agentes MCP.

### 1.4 Servidor e Integración MCP (Model Context Protocol)
- **Decisión**: Servidor MCP en Python (`FastMCP` o SDK oficial `mcp`) que expone herramientas reutilizando directamente los servicios de dominio de la aplicación (`services/`).
- **Rationale**:
  - Cumple los Principios I y VI de la Constitución: las herramientas MCP nunca invocan repositorios ni bases de datos directamente; invocan los mismos métodos del `ProductService`.
  - La herramienta recibe el contexto de identidad del usuario autenticado (token JWT o sesión validada) y asegura que las respuestas estén aisladas a su `user_id`.
  - Herramientas a proveer:
    1. `consultar_inventario`: Consulta el catálogo de productos del usuario autenticado con soporte para filtros.
    2. `consultar_productos_stock_bajo`: Filtra de manera específica los productos críticos (`cantidad_disponible <= cantidad_minima`).
- **Alternativas consideradas**:
  - *Acceso directo de MCP a SQLite*: Estrictamente prohibido por la Constitución (Principio I).

### 1.5 Estrategia de Pruebas y Cobertura
- **Decisión**: **pytest** con **pytest-cov**, implementando un repositorio falso en memoria (`FakeProductRepository` y `FakeUserRepository`) sin `unittest.mock`.
- **Rationale**:
  - Cumple estrictamente el Principio VII de la Constitución: pruebas unitarias puras y deterministas de la lógica de negocio en `services` sin parchar con `unittest.mock`.
  - El repositorio falso almacena entidades en estructuras de datos en memoria (`dict[int, Product]`), respetando el mismo protocolo o interfaz que el repositorio real de SQLAlchemy.
  - Se incluye al menos una prueba de integración que interactúa con un motor SQLite real para verificar la creación de tablas, llaves foráneas y persistencia.
  - Control de calidad mediante umbrales en `pytest --cov=src/services --cov-fail-under=90 --cov=src --cov-fail-under=70`.
- **Alternativas consideradas**:
  - *Mocks con `unittest.mock.MagicMock`*: Prohibido explícitamente por la Constitución para las pruebas de servicios.

---

## 2. Invariantes de Dominio y Reglas de Negocio

1. **Aislamiento Multi-inquilino**:
   - Todo servicio de productos recibe como primer parámetro el `user_id` autenticado.
   - Cualquier intento de acceder o mutar un `product_id` que no pertenezca a `user_id` genera una excepción de dominio `ProductNotFoundError` (retornando HTTP 404 para evitar fugas de información).
2. **Cantidades No Negativas y Alerta de Stock Mínimo**:
   - `cantidad_disponible >= 0` y `cantidad_minima >= 0`. Ambas deben ser enteros estrictos (`int >= 0`).
   - Se permite explícitamente que `cantidad_disponible < cantidad_minima` para modelar el consumo real de existencias.
   - Se activa la alerta de stock crítico (`is_low_stock = True`) cuando `cantidad_disponible <= cantidad_minima`.
   - Cualquier operación (creación, ajuste o edición) que intente fijar o reducir la cantidad disponible por debajo de cero (`< 0`) genera `InvariantViolationError` (HTTP 400 Bad Request).
   - En la edición de productos (`update_product`), se revalidan ambas cantidades como no negativas.
3. **Unicidad de Nombre por Usuario y Manejo Limpio**:
   - Dentro del inventario de un mismo usuario, no deben existir dos productos con el mismo nombre normalizado.
   - Ante colisiones de nombre, `ProductService` arroja `DuplicateEntityError` (HTTP 400 Bad Request con mensaje descriptivo) sin exponer excepciones internas de base de datos ni provocar caídas HTTP 500.

---

## 3. Resumen de Resoluciones Técnicas

| Área | Solución Adoptada | Justificación Constitucional |
|---|---|---|
| Arquitectura | Capas desacopladas (`routers`, `mcp`, `services`, `repositories`, `models`, `schemas`, `utils`) | Principio I |
| Negocio | Lógica e invariantes en `services` con repositorio inyectado | Principio II |
| Autorización | Filtrado estricto por `user_id` en cada método de `services` (anti-BOLA) | Principio III |
| Seguridad | OAuth2 + JWT + Bcrypt + `.env` protegido | Principio IV |
| Stock y Alertas | Cantidades `>= 0`, permisión de `disponible < minima` y alerta en `disponible <= minima` | Principio V (v2.0.0) |
| MCP | Tools que invocan `services` validando identidad | Principio VI |
| Testing | Fake repo en memoria + Test BD real + Cobertura >= 90%/70% | Principio VII |
