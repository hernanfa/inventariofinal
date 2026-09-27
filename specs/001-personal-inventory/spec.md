# Feature Specification: Inventario Personal

**Feature Branch**: `001-personal-inventory`

**Created**: 2026-09-25

**Status**: Draft

**Input**: User description: "Crear una aplicación web de Inventario Personal. Cada usuario debe poder registrarse, iniciar sesión y administrar únicamente sus propios productos. Debe poder crear, consultar, editar y eliminar productos con nombre, descripción opcional, cantidad disponible y cantidad mínima. Ambas cantidades deben ser enteros no negativos. El sistema debe mostrar los productos cuya cantidad disponible sea menor o igual a la cantidad mínima. Los usuarios no pueden consultar ni modificar productos ajenos. Incluir una herramienta MCP para consultar el inventario del usuario autenticado, reutilizando las mismas reglas de negocio del servicio. Describir flujos, criterios de aceptación y casos límite verificables; no elegir todavía tecnologías ni detalles de implementación."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registro e Inicio de Sesión de Usuario (Priority: P1)

Como nuevo usuario del sistema, quiero registrar una cuenta personal e iniciar sesión de manera segura para disponer de un espacio privado y protegido donde gestionar mi propio inventario sin interferencias de otros usuarios.

**Why this priority**: Es el cimiento esencial de seguridad y privacidad del sistema; sin autenticación no es posible garantizar el aislamiento de datos por usuario requerido por las normas del proyecto.

**Independent Test**: Puede probarse de forma independiente registrando un nuevo usuario con credenciales válidas, iniciando sesión y verificando el acceso al espacio privado de trabajo, así como verificando que credenciales incorrectas impiden el acceso.

**Acceptance Scenarios**:

1. **Given** un visitante en la pantalla de registro, **When** proporciona un nombre de usuario/correo no registrado previamente y una contraseña segura (mínimo 8 caracteres), **Then** el sistema crea la cuenta con éxito y permite al usuario iniciar sesión.
2. **Given** un usuario previamente registrado, **When** ingresa sus credenciales correctas en la pantalla de inicio de sesión, **Then** el sistema valida su identidad, establece su sesión activa y le presenta su panel principal de inventario.
3. **Given** un usuario que intenta iniciar sesión, **When** suministra una contraseña incorrecta o un usuario inexistente, **Then** el sistema deniega el acceso y muestra un mensaje de error claro sin comprometer detalles internos.

---

### User Story 2 - Gestión Básica de Productos del Inventario (Priority: P1)

Como usuario autenticado, quiero crear, consultar, actualizar y eliminar productos de mi inventario personal con su nombre, descripción opcional, cantidad disponible y cantidad mínima para mantener un control exacto de mis existencias.

**Why this priority**: Es el núcleo funcional del valor de la aplicación (MVP) para la gestión operativa del inventario personal.

**Independent Test**: Puede probarse creando un producto con valores válidos, verificando que aparece en el listado personal, modificando su nombre o descripción, y posteriormente eliminándolo para constatar que desaparece del listado.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado en el formulario de creación, **When** ingresa un nombre obligatorio no duplicado, una descripción opcional, una cantidad disponible válida (entero >= 0) y una cantidad mínima válida (entero >= 0), **Then** el producto es guardado y se muestra de inmediato en su lista personal de inventario.
2. **Given** un usuario autenticado que tiene productos registrados, **When** accede a su catálogo de productos, **Then** el sistema lista únicamente los productos que le pertenecen, detallando nombre, descripción, cantidad disponible y cantidad mínima.
3. **Given** un usuario autenticado visualizando el detalle de un producto propio, **When** modifica su nombre, descripción o cantidades y confirma el cambio, **Then** el sistema revalida que ambas cantidades sean enteros no negativos (`>= 0`), que no colisione con otro producto del mismo nombre y actualiza la información.
4. **Given** un usuario autenticado visualizando un producto de su propiedad, **When** confirma la solicitud de eliminación del producto, **Then** el producto es retirado definitivamente del inventario personal y deja de estar visible en el sistema.

---

### User Story 3 - Visualización de Productos con Existencias Críticas o Bajas (Priority: P2)

Como usuario autenticado, quiero ver claramente y de forma destacada los productos cuya cantidad disponible sea menor o igual a la cantidad mínima configurada para saber a tiempo cuándo debo reabastecer inventario antes de quedarme sin existencias.

**Why this priority**: Aporta valor directo de negocio en la toma de decisiones preventivas de abastecimiento.

**Independent Test**: Puede probarse configurando un producto con cantidad disponible igual a la mínima y otro con cantidad disponible menor a la mínima, comprobando que ambos son categorizados y presentados con advertencia visual de existencia crítica en la interfaz del usuario.

**Acceptance Scenarios**:

1. **Given** un usuario con productos donde la cantidad disponible es igual a la cantidad mínima (`cantidad_disponible == cantidad_minima`), **When** consulta su panel de inventario, **Then** el sistema muestra esos productos resaltados con un indicador de stock crítico / mínimo alcanzado.
2. **Given** un usuario con productos donde la cantidad disponible es estrictamente menor a la cantidad mínima (`cantidad_disponible < cantidad_minima`), **When** consulta la sección o filtro de existencias críticas, **Then** el sistema lista dichos productos señalando la necesidad urgente de reposición.
3. **Given** un usuario con productos donde la cantidad disponible supera a la mínima (`cantidad_disponible > cantidad_minima`), **When** consulta el filtro de existencias críticas, **Then** esos productos no se presentan como críticos.

---

### User Story 4 - Ajuste de Existencias y Control de Stock No Negativo (Priority: P2)

Como usuario autenticado, quiero ajustar las existencias disponibles de mis productos de forma flexible, permitiendo reducciones por consumo que desciendan por debajo del stock mínimo para detectar desabastecimientos pero impidiendo existencias negativas.

**Why this priority**: Permite registrar el consumo real de existencias garantizando que el stock nunca sea negativo (`cantidad_disponible >= 0`).

**Independent Test**: Puede probarse realizando ajustes de existencias válidos que dejen la cantidad disponible por encima, igual o por debajo de la mínima, comprobando que se actualiza y actualiza la alerta de stock bajo; y probando un ajuste con cantidad negativa o que intente dejar el stock disponible por debajo de cero, verificando su rechazo inmediato.

**Acceptance Scenarios**:

1. **Given** un producto con cantidad disponible de 10 y cantidad mínima de 3, **When** el usuario realiza un ajuste reduciendo la cantidad disponible a 5 (5 >= 3), **Then** el sistema actualiza la cantidad disponible a 5 y confirma la operación con éxito manteniendo el estado sin alerta crítica.
2. **Given** un producto con cantidad disponible de 10 y cantidad mínima de 5, **When** el usuario realiza un ajuste por consumo reduciendo la cantidad disponible a 2 (2 < 5), **Then** el sistema actualiza la cantidad disponible a 2, confirma la operación y activa de inmediato la alerta visual de stock crítico (`is_low_stock = true`).
3. **Given** un usuario que intenta ajustar existencias, **When** introduce valores negativos (p. ej. -1) o valores que dejarían la cantidad disponible menor a cero, **Then** el sistema bloquea la operación con un error de validación claro indicando que la cantidad disponible no puede ser negativa.

---

### User Story 5 - Aislamiento Estricto entre Usuarios (Priority: P1)

Como usuario del sistema, quiero tener la absoluta certeza de que ningún otro usuario pueda consultar, alterar o eliminar mis productos, ni que yo pueda interactuar con inventarios ajenos, para proteger la privacidad e integridad de mis datos.

**Why this priority**: Requisito crítico no negociable de seguridad y cumplimiento de la constitución del sistema (prevención de BOLA/IDOR).

**Independent Test**: Puede probarse creando dos usuarios independientes A y B con sus respectivos productos; verificar que el usuario A no puede ver los productos de B en listas ni acceder a ellos mediante identificadores directos, y viceversa.

**Acceptance Scenarios**:

1. **Given** dos usuarios registrados A y B con productos creados respectivamente, **When** el usuario A consulta su inventario, **Then** el sistema muestra únicamente los productos creados por A y ningún producto de B.
2. **Given** un producto perteneciente al usuario B, **When** el usuario A intenta consultar directamente el detalle de dicho producto, **Then** el sistema deniega el acceso indicando que el recurso no existe o no está autorizado (HTTP 404).
3. **Given** un producto perteneciente al usuario B, **When** el usuario A intenta editar o eliminar dicho producto mediante cualquier vía, **Then** el sistema rechaza la acción, mantiene el producto sin cambios y no revela información de pertenencia ajena.

---

### User Story 6 - Consulta de Inventario mediante Herramienta MCP Segura (Priority: P3)

Como usuario que interactúa mediante un asistente o agente inteligente, quiero que el agente disponga de una herramienta MCP para consultar mi inventario personal reutilizando las mismas reglas de negocio y aislamiento, para obtener asistencia contextual sobre mis existencias sin comprometer la seguridad.

**Why this priority**: Habilita la integración con agentes de IA conservando el mismo modelo de negocio y control de identidad.

**Independent Test**: Puede probarse invocando la herramienta MCP con el contexto de identidad del usuario y verificando que devuelve exactamente la lista de productos que pertenecen a dicho usuario con sus estados de stock, aplicando las mismas reglas de visualización que la aplicación web.

**Acceptance Scenarios**:

1. **Given** una sesión de agente que cuenta con la identidad verificada de un usuario autenticado, **When** se ejecuta la herramienta MCP de consulta de inventario, **Then** la herramienta devuelve el listado de productos exclusivos de dicho usuario con sus cantidades actuales y marcas de stock bajo.
2. **Given** una invocación a la herramienta MCP sin identidad de usuario válida o con credenciales expiradas, **When** se solicita la consulta de inventario, **Then** la herramienta rechaza la ejecución indicando falta de autenticación válida.
3. **Given** una invocación a la herramienta MCP por parte del usuario A, **When** solicita productos, **Then** en ningún caso se incluyen ni se exponen productos que pertenezcan al usuario B.

---

### Edge Cases

- **Valores negativos o decimales**: ¿Qué sucede si un usuario introduce cantidades negativas (p. ej. -5) o valores decimales (p. ej. 2.5)? El sistema valida estrictamente los campos antes de procesar y rechaza la entrada, exigiendo números enteros mayores o iguales a cero (`>= 0`).
- **Cantidad disponible menor que mínima**: Se permite explícitamente tanto en creación como en ajuste y edición para reflejar desabastecimientos reales, activando de inmediato la alerta de stock crítico (`cantidad_disponible <= cantidad_minima`).
- **Nombres duplicados del mismo usuario**: ¿Qué sucede si un usuario intenta crear o renombrar un producto con un nombre que ya existe en su propio inventario? El sistema captura la colisión de nombres y responde con un mensaje de error claro y amigable (HTTP 400 Bad Request: `"Ya existe un producto con el nombre '[nombre]' en tu inventario"`), evitando cualquier excepción interna no controlada o error HTTP 500 de base de datos. Dos usuarios distintos SÍ pueden tener productos con el mismo nombre en sus respectivos inventarios.
- **Nombre vacío o compuesto por espacios**: Si se intenta crear o editar un producto con un nombre vacío o únicamente con espacios en blanco, el sistema lo rechaza exigiendo al menos un carácter visible.
- **Inventario vacío**: ¿Cómo responde el sistema cuando un usuario recién registrado o sin productos consulta su inventario o ejecuta la herramienta MCP? El sistema muestra un estado vacío claro y descriptivo, indicando que aún no existen productos registrados y facilitando la acción de crear el primero.
- **Acceso anónimo o sesión caducada**: ¿Qué sucede cuando un usuario cuya sesión ha expirado intenta realizar una consulta, modificación o borrado? El sistema interrumpe la operación, protege los datos y responde HTTP 401 Unauthorized.
- **Eliminación concurrente**: ¿Qué ocurre si un usuario intenta modificar o borrar un producto que ya fue eliminado en otra pestaña o cliente? El sistema informa que el producto ya no se encuentra disponible (HTTP 404 Not Found) sin generar inconsistencias.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE permitir a los usuarios registrar una cuenta personal proporcionando un identificador/correo único y una credencial de acceso segura (mínimo 8 caracteres).
- **FR-002**: El sistema DEBE autenticar a los usuarios registrados, mantener una sesión segura y verificar su identidad en cada interacción.
- **FR-003**: El sistema DEBE asociar cada producto creado de forma unívoca y exclusiva al usuario autenticado que lo originó (`user_id`).
- **FR-004**: El sistema DEBE aislar estrictamente los datos entre usuarios: ningún usuario PUEDE consultar, filtrar, editar ni eliminar productos pertenecientes a otros usuarios.
- **FR-005**: El sistema DEBE permitir al usuario autenticado registrar nuevos productos con los siguientes campos:
  - Nombre del producto (obligatorio, texto no vacío, 1 a 100 caracteres).
  - Descripción (opcional, texto hasta 500 caracteres).
  - Cantidad disponible (obligatorio, número entero no negativo `>= 0`).
  - Cantidad mínima (obligatorio, número entero no negativo `>= 0`).
- **FR-006**: El sistema DEBE validar de forma obligatoria que tanto la cantidad disponible como la cantidad mínima sean números enteros mayores o iguales a cero (`>= 0`).
- **FR-007**: El sistema DEBE permitir que la cantidad disponible sea menor que la cantidad mínima (`cantidad_disponible < cantidad_minima`). Cualquier operación (creación, edición o ajuste) que pretenda fijar o reducir la cantidad disponible por debajo de cero (`< 0`) DEBE ser rechazada de inmediato.
- **FR-008**: El sistema DEBE permitir al usuario autenticado listar todos sus productos con soporte para paginación (`skip`, `limit`) y filtros de búsqueda.
- **FR-009**: El sistema DEBE identificar y presentar de manera visualmente diferenciada y filtrable aquellos productos cuya cantidad disponible sea menor o igual a su cantidad mínima (`cantidad_disponible <= cantidad_minima`).
- **FR-010**: El sistema DEBE permitir al usuario autenticado editar los atributos de sus productos existentes, revalidando de forma obligatoria que ambas cantidades continúen siendo enteros no negativos (`>= 0`).
- **FR-011**: El sistema DEBE verificar la unicidad del nombre de producto dentro del inventario del mismo usuario y responder con un error descriptivo de negocio (HTTP 400 Bad Request) ante duplicados, sin provocar errores internos ni revelar detalles de base de datos.
- **FR-012**: El sistema DEBE permitir al usuario autenticado eliminar productos de su propio inventario tras una confirmación explícita.
- **FR-013**: El sistema DEBE proporcionar herramientas MCP para agentes que permitan consultar el inventario del usuario autenticado, reutilizando exactamente las mismas reglas de negocio, filtros de usuario e indicadores de existencias mínimas.
- **FR-014**: El sistema DEBE emitir mensajes de error claros, descriptivos y comprensibles para el usuario final cuando se infrinjan validaciones de datos o reglas de negocio, sin revelar detalles internos del sistema.

### Key Entities *(include if feature involves data)*

- **Usuario (User Account)**:
  - Representa a la persona propietaria de un inventario personal dentro del sistema.
  - Atributos conceptuales: Identificador único, nombre de usuario único (3 a 50 caracteres), correo electrónico único, credenciales de acceso hasheadas con bcrypt, fecha de registro y estado de la cuenta.
  - Relaciones: Posee una colección de cero a muchos Productos.

- **Producto (Inventory Item)**:
  - Representa un artículo o bien individual catalogado dentro del inventario del usuario.
  - Atributos conceptuales: Identificador único, referencia al Usuario propietario (`user_id`), nombre del producto (1 a 100 caracteres, único por usuario), descripción detallada (opcional), cantidad disponible (entero >= 0), cantidad mínima requerida (entero >= 0), estado de existencia crítica (calculado: `cantidad_disponible <= cantidad_minima`), fecha de creación y fecha de última modificación.
  - Relaciones: Pertenece estrictamente a un único Usuario.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario puede completar el proceso de registro y acceder a su inventario vacío en menos de 60 segundos.
- **SC-002**: El 100 % de los intentos de acceso, consulta, edición o borrado cruzado entre usuarios distintos son bloqueados efectivamente, garantizando cero incidentes de fuga de datos entre usuarios.
- **SC-003**: El 100 % de los productos cuya cantidad disponible es menor o igual a la cantidad mínima son señalizados inmediatamente como críticos (`is_low_stock = true`) tanto en la interfaz de usuario como en la salida de la herramienta MCP.
- **SC-004**: El 100 % de los intentos de ingresar cantidades negativas (`< 0`), no enteras o de realizar ajustes que resulten en existencias negativas son rechazados antes de generar cambios de estado.
- **SC-005**: El 100 % de los intentos de crear o renombrar un producto con un nombre duplicado perteneciente al mismo usuario son respondidos con error HTTP 400 Bad Request controlado, sin provocar errores HTTP 500 de base de datos.
- **SC-006**: La herramienta MCP devuelve los datos de inventario del usuario autenticado reflejando con exactitud del 100 % el mismo contenido y estado visible en la aplicación web.

## Assumptions

- Cada usuario administra su propio catálogo de productos de forma independiente; no se contemplan en esta etapa inventarios colaborativos ni roles de administración compartida.
- La unicidad del nombre de producto se evalúa dentro del ámbito de cada usuario (dos usuarios distintos pueden tener un producto con el mismo nombre en sus respectivos inventarios).
- Las herramientas MCP operan bajo el contexto de identidad del usuario previamente autenticado y comparten el mismo ciclo de vida de sesión o autorización.
- La unidad de medida de las existencias es discreta (unidades enteras), adecuada para conteo de inventario personal.
