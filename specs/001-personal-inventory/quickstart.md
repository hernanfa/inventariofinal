# Quickstart & Validation Guide: Inventario Personal

**Feature**: `specs/001-personal-inventory`  
**Date**: 2026-09-25  

Este documento describe los escenarios ejecutables paso a paso para validar la implementación completa del sistema de Inventario Personal, verificando los requerimientos funcionales y el cumplimiento constitucional (Constitución v2.0.0).

---

## 1. Requisitos Previos y Entorno

- **Python**: Versión 3.11 o superior.
- **Entorno virtual**: Crear y activar un entorno virtual:
  ```bash
  python -m venv venv
  # En Windows (PowerShell):
  .\venv\Scripts\Activate.ps1
  # En Linux/macOS:
  source venv/bin/activate
  ```
- **Instalación de dependencias**:
  ```bash
  pip install -r requirements.txt
  ```
- **Variables de Entorno (`.env`)**:
  Crear el archivo `.env` en la raíz del proyecto (basado en `.env.example` y verificado en `.gitignore`):
  ```env
  DATABASE_URL=sqlite:///./inventario.db
  SECRET_KEY=clave_secreta_super_segura_para_jwt_inventario_personal_12345
  ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=60
  ENVIRONMENT=development
  ```

---

## 2. Ejecución de la Suite de Pruebas y Cobertura

El Principio VII de la Constitución exige pruebas con repositorios falsos (sin `unittest.mock`), una prueba de integración con base de datos real y umbrales estrictos de cobertura:

```bash
# Ejecutar todas las pruebas con reporte de cobertura y verificación de umbrales
pytest --cov=src/services --cov-fail-under=90 --cov=src --cov-fail-under=70 -v
```

### Escenarios de Prueba Clave a Validar:
1. **Pruebas Unitarias de Servicios (`tests/unit/test_product_service.py`)**:
   - `FakeProductRepository` almacena datos en memoria.
   - Creación de producto exitosa con enteros no negativos (`>= 0`).
   - Revalidación de cantidades al actualizar producto.
   - Rechazo controlado con `DuplicateEntityError` (HTTP 400) si el usuario intenta crear o renombrar a un nombre duplicado en su inventario.
   - Aislamiento de usuario: el usuario A intenta consultar/actualizar un producto del usuario B y el servicio lanza `ProductNotFoundError`.
2. **Pruebas de Invariante No Negativo y Alerta de Stock (`tests/unit/test_stock_invariant.py`, `tests/unit/test_stock_alerts.py`)**:
   - Se permite que `cantidad_disponible < cantidad_minima` y activa la alerta `is_low_stock = True`.
   - Rechazo con error de dominio (`InvariantViolationError`) cuando se intenta fijar o reducir `cantidad_disponible < 0`.
3. **Pruebas de Integración con Base de Datos Real (`tests/integration/test_db_integration.py`)**:
   - Inicialización de base de datos SQLite real.
   - Persistencia de un usuario, inserción de productos con llave foránea y verificación de restricciones de unicidad (`uq_user_product_name`) y no negatividad.
4. **Pruebas de Herramientas MCP (`tests/unit/test_mcp_tools.py`)**:
   - Invocación de `consultar_inventario` pasando token válido y validando que devuelva únicamente los productos del usuario autenticado con alertas correctas.

---

## 3. Ejecución de la API Web (FastAPI)

Iniciar el servidor de desarrollo:
```bash
uvicorn src.main:app --reload --port 8000
```

- Documentación interactiva Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Documentación alternativa ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Flujo de Validación Manual End-to-End:

1. **Registrar Usuario A**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username": "alice", "email": "alice@example.com", "password": "Password123!"}'
   ```
2. **Iniciar Sesión y Obtener Token (Alice)**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=alice&password=Password123!"
   # Guardar access_token recibido en una variable TOKEN_ALICE
   ```
3. **Crear Producto con Existencia Normal**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/products \
     -H "Authorization: Bearer $TOKEN_ALICE" \
     -H "Content-Type: application/json" \
     -d '{"name": "Manzanas", "description": "Bolsa de 1kg", "cantidad_disponible": 10, "cantidad_minima": 2}'
   ```
4. **Validar Rechazo de Cantidades Negativas**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/products \
     -H "Authorization: Bearer $TOKEN_ALICE" \
     -H "Content-Type: application/json" \
     -d '{"name": "Leche", "cantidad_disponible": -1, "cantidad_minima": 3}'
   # Debe responder HTTP 422 o 400 Bad Request
   ```
5. **Crear Producto con Stock Bajo (`disponible <= minima`) y Verificar Filtro**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/products \
     -H "Authorization: Bearer $TOKEN_ALICE" \
     -H "Content-Type: application/json" \
     -d '{"name": "Café", "cantidad_disponible": 1, "cantidad_minima": 3}'
   # Se crea con éxito y con is_low_stock = true

   # Consultar productos críticos
   curl -X GET "http://localhost:8000/api/v1/products?low_stock=true" \
     -H "Authorization: Bearer $TOKEN_ALICE"
   ```
6. **Validar Rechazo Controlado ante Nombre Duplicado**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/products \
     -H "Authorization: Bearer $TOKEN_ALICE" \
     -H "Content-Type: application/json" \
     -d '{"name": "Café", "cantidad_disponible": 5, "cantidad_minima": 1}'
   # Debe responder HTTP 400 Bad Request: "Ya existe un producto con el nombre 'Café' en tu inventario"
   ```
7. **Validar Aislamiento de Usuario (Bob no puede ver los productos de Alice)**:
   - Registrar y autenticar a `bob`.
   - Listar productos con el token de `bob`: la lista debe estar vacía (`items: []`).
   - Intentar consultar `GET /api/v1/products/{id_producto_alice}` con el token de `bob`: debe devolver `404 Not Found`.

---

## 4. Validación de Herramientas MCP

Ejecutar el servidor MCP para agentes:
```bash
python -m src.mcp.server
```
Invocar la tool `consultar_inventario` pasando el token de sesión y confirmar que retorna la misma información estructurada respetando el aislamiento y las reglas de dominio.
