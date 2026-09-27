# Inventario Personal

API REST y servidor MCP para gestionar un inventario por usuario con autenticación JWT, alerta de stock bajo y pruebas automatizadas.

## Requisitos

Python 3.13 y pip.

## Inicio en PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Antes de iniciar, cambie `SECRET_KEY` en `.env` por un valor aleatorio privado. No suba `.env` al repositorio.

```powershell
pytest --cov=src.services --cov=src --cov-report=term-missing -v
uvicorn src.main:app --reload --port 8000
```

Documentación REST: http://127.0.0.1:8000/docs. En otra terminal, desde la raíz del proyecto y con el entorno virtual activo, inicie MCP: `python -m src.mcp.server`. Las herramientas `consultar_inventario` y `consultar_productos_stock_bajo` reciben el JWT del usuario.

La eliminación de productos requiere `DELETE /api/v1/products/{id}?confirm=true`.

## Diseño y pruebas

La constitución está en `.specify/memory/constitution.md`; la especificación, plan y tareas están en `specs/001-personal-inventory/`. La suite incluye pruebas unitarias, de integración REST y MCP.
