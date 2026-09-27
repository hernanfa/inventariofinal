# REST API Contracts: Inventario Personal

**Feature**: `specs/001-personal-inventory`  
**Date**: 2026-09-25  
**Version**: 2.0.0  

---

## 1. Módulo de Autenticación (`/api/v1/auth`)

### 1.1 Registrar Usuario
- **Ruta**: `POST /api/v1/auth/register`
- **Cabeceras**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "username": "usuario1",
    "email": "usuario1@example.com",
    "password": "PasswordSeguro123!"
  }
  ```
- **Respuestas**:
  - `201 Created`:
    ```json
    {
      "id": 1,
      "username": "usuario1",
      "email": "usuario1@example.com",
      "created_at": "2026-09-25T10:00:00Z"
    }
    ```
  - `400 Bad Request`: `{"detail": "El nombre de usuario o correo ya se encuentra registrado"}`
  - `422 Unprocessable Entity`: Error de formato de validación en esquemas Pydantic (p. ej. contraseña menor a 8 caracteres).

### 1.2 Iniciar Sesión (OAuth2 Token)
- **Ruta**: `POST /api/v1/auth/login`
- **Cabeceras**: `Content-Type: application/x-www-form-urlencoded`
- **Request Body**:
  ```text
  username=usuario1&password=PasswordSeguro123!
  ```
- **Respuestas**:
  - `200 OK`:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI...",
      "token_type": "bearer",
      "expires_in": 1800
    }
    ```
  - `401 Unauthorized`: `{"detail": "Credenciales inválidas"}`

### 1.3 Obtener Perfil Autenticado
- **Ruta**: `GET /api/v1/auth/me`
- **Cabeceras**: `Authorization: Bearer <token>`
- **Respuestas**:
  - `200 OK`:
    ```json
    {
      "id": 1,
      "username": "usuario1",
      "email": "usuario1@example.com",
      "created_at": "2026-09-25T10:00:00Z"
    }
    ```
  - `401 Unauthorized`: Token ausente, inválido o expirado.

---

## 2. Módulo de Inventario (`/api/v1/products`)

Todas las operaciones en este módulo requieren cabecera `Authorization: Bearer <token>`.

### 2.1 Listar Productos Propios
- **Ruta**: `GET /api/v1/products`
- **Query Params**:
  - `low_stock: Optional[bool]` (si es `true`, filtra solo donde `cantidad_disponible <= cantidad_minima`)
  - `search: Optional[str]` (búsqueda por nombre o descripción)
  - `skip: int = 0`
  - `limit: int = 50`
- **Respuestas**:
  - `200 OK`:
    ```json
    {
      "items": [
        {
          "id": 10,
          "user_id": 1,
          "name": "Café Colombiano",
          "description": "Café en grano 500g",
          "cantidad_disponible": 1,
          "cantidad_minima": 3,
          "is_low_stock": true,
          "created_at": "2026-09-25T10:15:00Z",
          "updated_at": "2026-09-25T10:15:00Z"
        }
      ],
      "total": 1,
      "total_low_stock": 1
    }
    ```

### 2.2 Crear Producto
- **Ruta**: `POST /api/v1/products`
- **Request Body**:
  ```json
  {
    "name": "Arroz Integral",
    "description": "Bolsa de 1kg",
    "cantidad_disponible": 2,
    "cantidad_minima": 5
  }
  ```
  *(Nota: Se permite que `cantidad_disponible < cantidad_minima`; en este caso, se crea con `is_low_stock = true`).*
- **Respuestas**:
  - `201 Created`: Objeto `ProductResponse` con el producto recién creado.
  - `400 Bad Request`:
    - `{"detail": "Ya existe un producto con el nombre 'Arroz Integral' en tu inventario"}` (captura controlada sin error 500).
    - `{"detail": "Las cantidades no pueden ser negativas"}`.
  - `422 Unprocessable Entity`: Cantidades negativas o datos de tipo inválido.

### 2.3 Obtener Detalle de Producto
- **Ruta**: `GET /api/v1/products/{id}`
- **Respuestas**:
  - `200 OK`: Objeto `ProductResponse`.
  - `404 Not Found`: `{"detail": "Producto no encontrado"}` (se devuelve también si el producto existe pero pertenece a otro usuario, garantizando el aislamiento).

### 2.4 Actualizar Producto
- **Ruta**: `PUT /api/v1/products/{id}`
- **Request Body**:
  ```json
  {
    "name": "Arroz Integral Premium",
    "description": "Bolsa de 1kg grano seleccionado",
    "cantidad_disponible": 4,
    "cantidad_minima": 5
  }
  ```
  *(Nota: La capa de servicio revalida que ambas cantidades sean enteros no negativos `>= 0`).*
- **Respuestas**:
  - `200 OK`: Objeto `ProductResponse` actualizado con `is_low_stock` recalculado.
  - `400 Bad Request`:
    - `{"detail": "Ya existe un producto con el nombre 'Arroz Integral Premium' en tu inventario"}`.
    - `{"detail": "Las cantidades deben ser enteros no negativos"}`.
  - `404 Not Found`: Producto no encontrado o ajeno.

### 2.5 Eliminar Producto
- **Ruta**: `DELETE /api/v1/products/{id}`
- **Respuestas**:
  - `204 No Content`: Eliminación confirmada.
  - `404 Not Found`: Producto inexistente o ajeno.

### 2.6 Ajustar Existencias de Producto
- **Ruta**: `POST /api/v1/products/{id}/adjust-stock`
- **Request Body**:
  ```json
  {
    "nueva_cantidad_disponible": 1,
    "motivo": "Consumo semanal"
  }
  ```
  *(Nota: Se permite que `nueva_cantidad_disponible < cantidad_minima`, marcando `is_low_stock: true`).*
- **Respuestas**:
  - `200 OK`: Objeto `ProductResponse` con la nueva cantidad disponible y recálculo de alerta de stock bajo.
  - `400 Bad Request`:
    - `{"detail": "La cantidad disponible no puede ser negativa"}` (si `nueva_cantidad_disponible < 0`).
  - `404 Not Found`: Producto inexistente o ajeno.
