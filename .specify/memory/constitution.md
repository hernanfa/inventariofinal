<!--
SYNC IMPACT REPORT
==================
- Version change: 1.0.0 → 2.0.0 (MAJOR bump)
- List of modified principles:
  * PRINCIPLE_5: V. Operaciones CRUD REST e Invariante de Stock No Negativo → V. Operaciones CRUD REST, Cantidades No Negativas y Alerta de Stock Mínimo.
    - Se redefine el invariante: cantidad disponible y cantidad mínima DEBEN ser enteros no negativos (>= 0).
    - Se permite explícitamente que la cantidad disponible sea menor que la mínima para posibilitar el consumo real y la detección de existencias críticas.
    - Se fija la regla de alerta de stock bajo cuando cantidad disponible <= cantidad mínima.
    - Se prohíbe de forma absoluta el stock negativo (< 0); cualquier ajuste o consumo que resulte en existencias menores a 0 DEBE ser rechazado de inmediato por services con HTTP 400.
- Added sections:
  * Ninguna
- Removed sections:
  * Ninguna
- Follow-up TODOs:
  * Ninguno.
-->

# Inventario Personal Constitution

## Core Principles

### I. Arquitectura por Capas Estricta
El sistema DEBE estructurarse de manera obligatoria en capas desacopladas con responsabilidades y flujo de dependencias unidireccionales:
- `routers`: Manejo de endpoints HTTP, recepción y validación de peticiones de entrada/salida y códigos de estado HTTP.
- `mcp`: Servidores y herramientas de Model Context Protocol (MCP) para la interacción con agentes de inteligencia artificial.
- `services`: Lógica de negocio, reglas de dominio y orquestación de operaciones.
- `repositories`: Abstracción de acceso a datos, consultas y persistencia.
- `models`: Entidades del dominio y definiciones de modelos de base de datos / ORM.
- `schemas`: Esquemas de validación, serialización y transferencia de datos (DTOs/Pydantic).
- `utils`: Funciones utilitarias transversales y auxiliares, estrictamente puras y sin lógica de negocio.

Las capas superiores PUEDEN invocar capas inferiores inmediatas, pero queda ESTRICTAMENTE PROHIBIDO que capas inferiores dependan de capas superiores, o que `routers` y `mcp` accedan directamente a `repositories` o `models` sin pasar por la capa `services`.
*Rationale*: Garantiza alta cohesión, bajo acoplamiento, mantenibilidad a largo plazo y facilidad para sustituir implementaciones de persistencia o transporte.

### II. Lógica de Negocio Centralizada en Services con Inyección de Dependencias
Toda regla de negocio, validación de dominio y cálculo de estado DEBE residir de manera exclusiva en la capa `services`.
- Las dependencias de acceso a datos (`repositories`) DEBEN ser inyectadas explícitamente en el constructor o método del servicio (Inversión de Dependencias).
- Ningún servicio DEBE instanciar directamente clientes de base de datos ni depender de implementaciones concretas de persistencia.
*Rationale*: Centraliza las decisiones críticas del negocio en un único lugar testeable y facilita el intercambio de repositorios por implementaciones en memoria durante pruebas unitarias.

### III. Aislamiento Multi-inquilino a Nivel de Usuario
Todos los productos y recursos de inventario DEBEN pertenecer de forma explícita e inequívoca al usuario autenticado que los administra (`user_id`).
- Toda operación de consulta, creación, actualización, eliminación o ajuste de inventario DEBE filtrar y validar de manera obligatoria el identificador del usuario autenticado (`user_id`).
- NINGÚN usuario PUEDE consultar, mutar ni eliminar productos o registros pertenecientes a otro usuario (prevención de BOLA / IDOR).
*Rationale*: Asegura la confidencialidad, privacidad e integridad de los datos de cada usuario en el sistema.

### IV. Seguridad, Autenticación OAuth2/JWT y Gestión de Secretos
La seguridad y el control de acceso DEBEN regirse por las siguientes reglas no negociables:
- La autenticación DEBE implementarse mediante OAuth2 con tokens de acceso JWT (JSON Web Tokens) firmados y con tiempo de expiración definido.
- Las contraseñas de los usuarios NUNCA deben persistirse en texto plano; DEBEN ser hasheadas con algoritmos criptográficos robustos y seguros (p. ej., bcrypt / argon2) con salt antes del almacenamiento.
- Toda clave secreta, cadena de conexión a base de datos y parámetro sensible DEBE cargarse exclusivamente mediante variables de entorno desde archivos `.env`.
- Los archivos `.env` y cualquier secreto NUNCA deben ser incluidos ni commiteados en el repositorio Git; DEBEN estar registrados en el archivo `.gitignore`.
*Rationale*: Protege la identidad de los usuarios y previene vulnerabilidades de fuga de credenciales o exposición de secretos en el control de versiones.

### V. Operaciones CRUD REST, Cantidades No Negativas y Alerta de Stock Mínimo
La API REST DEBE proveer operaciones estándar de creación, lectura, actualización y eliminación (CRUD) de productos, además de permitir el ajuste de existencias respetando las siguientes reglas de negocio:
- Tanto la `cantidad_disponible` como la `cantidad_minima` DEBEN ser obligatoriamente números enteros mayores o iguales a cero (`cantidad_disponible >= 0`, `cantidad_minima >= 0`).
- Se PERMITE explícitamente que la `cantidad_disponible` sea menor que la `cantidad_minima` (`cantidad_disponible < cantidad_minima`) para habilitar el consumo real de existencias y la detección de situaciones de abastecimiento crítico.
- El sistema DEBE identificar y señalizar una alerta de stock bajo cuando `cantidad_disponible <= cantidad_minima`.
- Invariante estricta de no negatividad: Queda estrictamente prohibido el inventario negativo. Cualquier solicitud de ajuste, creación o edición que pretenda fijar o reducir la `cantidad_disponible` por debajo de 0 DEBE ser rechazada de inmediato en la capa `services`, emitiendo una excepción de dominio y retornando el código de error HTTP adecuado (p. ej., 400 Bad Request o 422 Unprocessable Entity).
*Rationale*: Modela con realismo el ciclo de vida del inventario, permitiendo advertir desabastecimientos cuando las existencias descienden al umbral mínimo o por debajo de él, previniendo al mismo tiempo inventarios negativos inconsistentes.

### VI. Herramientas MCP Seguras con Reutilización de Servicios
El sistema DEBE exponer al menos dos herramientas (tools) Model Context Protocol (MCP) operativas para la interacción con agentes:
- Cada tool MCP DEBE reutilizar estrictamente la lógica de la capa `services`, sin duplicar código ni interactuar directamente con repositorios o bases de datos.
- Toda invocación de herramientas MCP DEBE autenticar y verificar de forma rigurosa la identidad del usuario, operando únicamente sobre los recursos permitidos para dicho usuario.
*Rationale*: Permite la extensibilidad del sistema hacia asistentes y agentes inteligentes manteniendo las mismas garantías de negocio, integridad y seguridad que los endpoints HTTP.

### VII. Pirámide de Pruebas con Repositorios Falsos, Test Real y Cobertura Obligatoria
La calidad del software DEBE ser verificada mediante una estrategia de pruebas estructurada y métricas cuantitativas:
- Pruebas unitarias en `services`: DEBEN utilizar implementaciones falsas de repositorios (fake repositories / in-memory test doubles). Queda ESTRICTAMENTE PROHIBIDO el uso de `unittest.mock` para simular repositorios en las pruebas de `services`.
- Pruebas de integración: DEBE existir al menos una prueba automatizada ejecutada contra una instancia de base de datos real para verificar la persistencia y contratos de repositorio.
- Umbrales mínimos de cobertura de código:
  - Capa `services`: Cobertura mínima obligatoria de **90 %**.
  - Cobertura global del proyecto: Cobertura mínima obligatoria de **70 %**.
- La suite de pruebas DEBE ejecutarse y pasar satisfactoriamente en su totalidad antes de fusionar o desplegar cualquier cambio.
*Rationale*: Garantiza un diseño modular y desacoplado mediante contratos claros, valida la persistencia real y previene regresiones con un estándar alto de cobertura comprobable.

## Requisitos Técnicos y de Seguridad
- El entorno de ejecución DEBE basarse en estándares modernos de Python con tipado estricto (type hints) y validación declarativa mediante esquemas Pydantic.
- Las dependencias externas DEBEN mantenerse mínimas, auditadas y gestionadas a través del archivo de dependencias del proyecto.
- Todo endpoint o herramienta DEBE registrar logs estructurados de errores sin volcar datos personales sensibles ni secretos.

## Flujo de Trabajo y Quality Gates
- Todo cambio de código DEBE someterse a una revisión de cumplimiento constitucional antes de integrarse.
- Las compuertas de calidad (Quality Gates) exigen:
  1. Paso del 100 % de las pruebas unitarias e integración.
  2. Cobertura mínima >= 90 % en `services` y >= 70 % global.
  3. Ausencia de secretos en el código fuente y cumplimiento estricto del aislamiento por usuario.

## Governance
Esta constitución es la máxima norma de diseño y arquitectura del proyecto Inventario Personal y prevalece sobre cualquier otra decisión o conveniencia técnica puntual.
- **Procedimiento de Enmienda**: Toda modificación o adición de principios DEBE documentarse formalmente, especificar su impacto en el diseño existente y ejecutarse a través de la herramienta de gobernanza de Spec Kit (`/speckit-constitution`).
- **Política de Versiones**: Las versiones de la constitución siguen el estándar Semantic Versioning (MAJOR.MINOR.PATCH):
  - **MAJOR**: Cambios incompatibles, eliminación o reemplazo de principios existentes.
  - **MINOR**: Incorporación de nuevos principios o expansión material de directrices existentes.
  - **PATCH**: Correcciones ortográficas, mejoras de redacción y clarificaciones no semánticas.
- **Revisión de Cumplimiento**: Todas las especificaciones (`spec.md`), planes (`plan.md`), tareas (`tasks.md`) y revisiones de código (PRs) DEBEN ser auditados contra estos principios de manera obligatoria.

**Version**: 2.0.0 | **Ratified**: 2026-09-25 | **Last Amended**: 2026-09-25
