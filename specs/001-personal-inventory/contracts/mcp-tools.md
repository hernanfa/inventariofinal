# Model Context Protocol (MCP) Tools Contract: Inventario Personal

**Feature**: `specs/001-personal-inventory`  
**Date**: 2026-09-25  
**Version**: 1.0.0  

---

## 1. Principios de Integración MCP

De acuerdo con la Constitución del Proyecto (Principios I y VI):
- Las herramientas MCP **NUNCA** interactúan directamente con la base de datos ni con la capa de repositorios.
- Cada herramienta MCP invoca métodos de la capa `services` (`ProductService`, `AuthService`).
- La identidad del usuario DEBE ser verificada en cada invocación mediante token de autenticación o contexto seguro de sesión, garantizando que el agente solo acceda a los recursos del usuario autenticado.

---

## 2. Herramientas Expuestas (Tools)

### 2.1 Herramienta `consultar_inventario`
Permite a un agente de inteligencia artificial consultar el listado de productos pertenecientes al usuario autenticado, con opciones de filtrado y búsqueda.

- **Nombre de la herramienta**: `consultar_inventario`
- **Descripción**: "Consulta los productos del inventario personal del usuario autenticado, indicando cantidades disponibles, mínimas y alertas de stock bajo."
- **Parámetros de Entrada (Schema JSON)**:
  ```json
  {
    "type": "object",
    "properties": {
      "token": {
        "type": "string",
        "description": "Token JWT de autenticación del usuario"
      },
      "solo_stock_bajo": {
        "type": "boolean",
        "description": "Si es True, devuelve exclusivamente productos donde cantidad_disponible <= cantidad_minima",
        "default": false
      },
      "busqueda": {
        "type": "string",
        "description": "Término de texto opcional para filtrar por nombre o descripción"
      }
    },
    "required": ["token"]
  }
  ```
- **Salida Exitosa (Estructura de Retorno)**:
  ```json
  {
    "status": "success",
    "usuario": "usuario1",
    "total_productos": 2,
    "total_stock_bajo": 1,
    "productos": [
      {
        "id": 10,
        "nombre": "Café Colombiano",
        "descripcion": "Café en grano 500g",
        "cantidad_disponible": 3,
        "cantidad_minima": 3,
        "alerta_stock_bajo": true
      },
      {
        "id": 11,
        "nombre": "Arroz Integral",
        "descripcion": "Bolsa de 1kg",
        "cantidad_disponible": 10,
        "cantidad_minima": 2,
        "alerta_stock_bajo": false
      }
    ]
  }
  ```
- **Errores Posibles**:
  - `TOKEN_INVALIDO`: Credenciales expiradas o ausentes.
  - `ACCESO_DENEGADO`: Fallo en la verificación de identidad.

---

### 2.2 Herramienta `consultar_productos_stock_bajo`
Herramienta especializada para asistentes que asisten en la gestión de compras o abastecimiento, filtrando directamente productos con necesidad urgente de reposición.

- **Nombre de la herramienta**: `consultar_productos_stock_bajo`
- **Descripción**: "Obtiene únicamente aquellos productos del usuario autenticado cuyas existencias han alcanzado o caído por debajo del umbral mínimo configurado."
- **Parámetros de Entrada (Schema JSON)**:
  ```json
  {
    "type": "object",
    "properties": {
      "token": {
        "type": "string",
        "description": "Token JWT de autenticación del usuario"
      }
    },
    "required": ["token"]
  }
  ```
- **Salida Exitosa (Estructura de Retorno)**:
  ```json
  {
    "status": "success",
    "usuario": "usuario1",
    "productos_criticos_count": 1,
    "productos_criticos": [
      {
        "id": 10,
        "nombre": "Café Colombiano",
        "cantidad_disponible": 3,
        "cantidad_minima": 3,
        "deficiencia": 0
      }
    ]
  }
  ```
