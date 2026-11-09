# App final RFHA-IES: cómo funciona, cómo se conecta con AWS y cómo probarla

Guía de la **aplicación final** (la red federada completa), separada de la demo del middleware. Explica qué hace cada pantalla, cómo se comunica el código con AWS, cómo se conecta todo para exponer y cómo probar cada historia de usuario (HU-01 a HU-05) **con clics, en pantalla**.

## Contenido

0. [La app final en 2 minutos](#0-la-app-final-en-2-minutos)
1. [Direcciones y claves](#1-direcciones-y-claves)
2. [Cómo se conecta todo](#2-cómo-se-conecta-todo)
3. [Cómo se comunica el código con AWS](#3-cómo-se-comunica-el-código-con-aws)
4. [Los datos: tres tablas en DynamoDB](#4-los-datos-tres-tablas-en-dynamodb)
5. [Seguridad: qué se protege y cómo](#5-seguridad-qué-se-protege-y-cómo)
6. [Qué hace cada historia de usuario](#6-qué-hace-cada-historia-de-usuario)
7. [Pruebas en pantalla, escena por escena](#7-pruebas-en-pantalla-escena-por-escena)
8. [Desplegar, actualizar, limpiar y borrar](#8-desplegar-actualizar-limpiar-y-borrar)
9. [Plan A (local) y Plan B (AWS)](#9-plan-a-local-y-plan-b-aws)
10. [Problemas frecuentes](#10-problemas-frecuentes)
11. [Preguntas probables](#11-preguntas-probables)

---

## 0. La app final en 2 minutos

**Qué es.** El sistema completo de la red: una universidad se **registra**, el administrador la **aprueba** y le entrega una clave, la universidad **carga los historiales** de sus estudiantes y cada estudiante **autoriza** (o **revoca**) que una universidad vea su historial. Todo con cuatro pantallas.

| Pantalla | Quién la usa | Historia | Dirección |
|---|---|---|---|
| **Registro** | Representante de una universidad | HU-01 | `/registro-nodo` |
| **Administración** | Administrador general de la red | HU-02 | `/admin` |
| **Panel del nodo** | Universidad ya aprobada | HU-03 | `/panel-nodo` |
| **Portal del estudiante** | Estudiante | HU-04 y HU-05 | `/portal-estudiante` |

**Cómo se relaciona con la demo.** La demo (`docs/DEMO.md`) muestra cómo el middleware **valida un permiso** al consultar un historial. La app final construye lo que viene **antes**: quién es parte de la red, de dónde salen los historiales y cómo nace y muere el permiso. La consulta federada completa llega con HU-06 y HU-07, que reutilizarán el token creado aquí.

**Lo que ya funciona:** HU-01 a HU-05. **Lo que falta:** consulta federada (HU-06), bloqueo (HU-07), réplica (HU-08), auditoría (HU-09) y pulido de la interfaz (HU-10).

---

## 1. Direcciones y claves

| | Dirección |
|---|---|
| **App final en AWS** | https://ypybm0azfg.execute-api.us-east-2.amazonaws.com (abre `/registro-nodo`) |
| Registro | https://ypybm0azfg.execute-api.us-east-2.amazonaws.com/registro-nodo |
| Administración | https://ypybm0azfg.execute-api.us-east-2.amazonaws.com/admin |
| Panel del nodo | https://ypybm0azfg.execute-api.us-east-2.amazonaws.com/panel-nodo |
| Portal del estudiante | https://ypybm0azfg.execute-api.us-east-2.amazonaws.com/portal-estudiante |
| Documentación de la API (Swagger) | https://ypybm0azfg.execute-api.us-east-2.amazonaws.com/docs |
| **App final en tu computador** | http://127.0.0.1:8001 (con `.\run-app.cmd`) |

**Claves que existen (ninguna está en este repositorio):**

| Clave | Para qué sirve | Dónde está |
|---|---|---|
| **ADMIN_KEY** | Entrar a `/admin`. | En el archivo `.env` de quien desplegó (es un archivo que **no** se sube a GitHub). Se entrega al equipo por mensaje privado. |
| **JWT_SECRET** | Firmar los tokens de los estudiantes. | En `.env` y en la variable de entorno de la Lambda. Nadie la escribe en pantalla. |
| **API Key del nodo** | Que una universidad suba historiales. | La crea el sistema al aprobar el nodo y se muestra **una sola vez** en `/admin`. |
| **Clave del estudiante** | Entrar al portal. | La define la universidad al cargar el historial (campo `password`). |

> **Aviso:** la dirección es pública. Cualquiera puede registrar una universidad de prueba, pero **no puede aprobarla** (hace falta `ADMIN_KEY`), ni cargar historiales (hace falta la API Key), ni ver nada de nadie (hace falta cédula y clave). Aun así, usa solo datos ficticios.

---

## 2. Cómo se conecta todo

```
 Navegador ──(1) HTTPS──▶ API Gateway ──(2) invoca──▶ Lambda "rfha-app" ──(3) HTTPS firmado──▶ DynamoDB
 (4 pantallas)           (HTTP API)                  Python 3.12                              ├─ NodesTable
                                                     FastAPI + Mangum                         ├─ RecordsTable
                                                          │                                   └─ TokensTable
                                                          └──(4)──▶ CloudWatch Logs (7 días)
```

| Tramo | Qué pasa | Protocolo y formato |
|---|---|---|
| **(1) Navegador → API Gateway** | El navegador pide una pantalla (`GET`) o envía datos (`POST`). | **HTTPS** (HTTP sobre TLS), estilo **REST**, datos en **JSON**. Las claves viajan en el cuerpo (cédula y clave) o en encabezados (`X-Admin-Key`, `X-Node-API-Key`), siempre cifradas por TLS. |
| **(2) API Gateway → Lambda** | API Gateway convierte la petición en un evento y despierta la Lambda. | Invocación de Lambda con **formato de carga 2.0** (JSON). |
| **Dentro de la Lambda** | **Mangum** traduce el evento al estándar **ASGI**; **FastAPI** valida, decide y responde. | Sin red: es código Python. |
| **(3) Lambda → DynamoDB** | El código lee y escribe las tablas. | **HTTPS** con la API JSON de DynamoDB, firmada con **Signature V4** usando credenciales temporales del rol de la Lambda. |
| **(4) Lambda → CloudWatch** | Lo que la función imprime queda en registros. | Interno de AWS; retención de 7 días. |

**Qué pone cada pieza:**

| Pieza | Responsabilidad |
|---|---|
| **API Gateway** | Es la puerta pública: HTTPS, dirección, y un límite de 20 peticiones por segundo contra abusos. No decide quién puede qué. |
| **Lambda + el código** | Es el **middleware**: valida los datos, comprueba claves, aplica las reglas y habla con la base. |
| **DynamoDB** | Guarda los datos y no sabe nada de reglas. |
| **IAM (rol de la Lambda)** | Limita a la Lambda a leer y escribir **solo sus tres tablas**. |
| **CloudFormation** | Crea y borra todo lo anterior a partir de `template.yaml`. |

---

## 3. Cómo se comunica el código con AWS

El código **no sabe que está en AWS**, salvo en tres puntos. Esto es lo que permite correrlo igual en tu computador.

### 3.1 La entrada: `handler`
En `src/app/main.py`, la última línea es `handler = Mangum(app, lifespan="off")`. En `template.yaml`, la Lambda declara `Handler: src.app.main.handler`. Cuando llega una petición, AWS llama a esa función con el evento; Mangum lo convierte en una petición normal para FastAPI. En tu computador, `uvicorn` hace de puerta de entrada y el resto del código no cambia.

### 3.2 La configuración: variables de entorno
La plantilla pasa estos valores a la Lambda y el código los lee en `src/app/config.py`:

| Variable | Valor en AWS | Qué cambia |
|---|---|---|
| `REPOSITORY_BACKEND` | `dynamodb` | Con `dynamodb` se usan las tablas; con `memory` (local) los datos viven en la memoria del programa. |
| `NODES_TABLE`, `RECORDS_TABLE`, `TOKENS_TABLE` | Nombres que genera CloudFormation | A qué tablas escribir. |
| `JWT_SECRET` | Parámetro `JwtSecret` del stack (oculto) | Firma de los tokens. |
| `ADMIN_KEY` | Parámetro `AdminKey` del stack (oculto) | Clave del administrador. |

Los secretos entran como **parámetros con `NoEcho`**: CloudFormation no los muestra en la consola ni en los registros. No hay Secrets Manager porque cobra.

### 3.3 El almacenamiento: repositorios
`src/app/repositories.py` define una interfaz por tabla con **dos implementaciones**: en memoria y en DynamoDB. Las rutas de la API piden un repositorio y no saben cuál reciben. La única parte que usa la biblioteca de AWS (`boto3`) es la implementación DynamoDB:

| Operación de la app | Llamada a DynamoDB | Permiso que necesita la Lambda |
|---|---|---|
| Registrar universidad (HU-01) | `Scan` (¿ya existe el NIT?) + `PutItem` | Leer y escribir `NodesTable` |
| Listar solicitudes (HU-02) | `Scan` con filtro por estado | Leer `NodesTable` |
| Aprobar nodo (HU-02) | `GetItem` + `UpdateItem` | Leer y escribir `NodesTable` |
| Identificar un nodo por su API Key (HU-03) | `Scan` con filtro por el hash | Leer `NodesTable` |
| Cargar historiales (HU-03) | `GetItem` + `PutItem` por estudiante | Leer y escribir `RecordsTable` |
| Ingresar al portal (HU-04) | `Scan` por cédula | Leer `RecordsTable` |
| Generar token (HU-04) | `GetItem` del destino + `PutItem` del token | `NodesTable` (leer), `TokensTable` (escribir) |
| Ver y revocar (HU-05) | `Scan`, `GetItem`, `UpdateItem` | Leer `RecordsTable`, leer y escribir `TokensTable` |

> **Por qué `Scan` y no un índice:** el catálogo es pequeño (decenas de universidades, cientos de estudiantes) y un índice agrega piezas. Si la red crece, se agrega un índice secundario y se cambia una función por repositorio.

### 3.4 Cómo se conecta la Lambda con DynamoDB sin claves
La Lambda no lleva contraseñas de AWS. CloudFormation crea un **rol de ejecución** con la política `DynamoDBCrudPolicy` sobre cada tabla, y AWS entrega a la función **credenciales temporales** del rol. `boto3` las encuentra solo. Por eso `repositories.py` solo escribe `boto3.resource("dynamodb")`.

### 3.5 Lo que NO hace el código
No llama a S3, Cognito, SES, KMS propio ni Secrets Manager. Menos servicios = menos costo y menos cosas que pueden fallar.

---

## 4. Los datos: tres tablas en DynamoDB

Todas en modo **bajo demanda** (se paga por uso real, sin capacidad reservada) y con el cifrado en reposo predeterminado de DynamoDB.

| Tabla | Clave | Qué guarda | Historia |
|---|---|---|---|
| **NodesTable** | `node_id` (ej. `IES-1A2B3C4D`) | NIT, nombre, dominio, correo, estado (`PENDIENTE_APROBACION` o `ACTIVO`), fecha, y tras aprobar: `api_key_hash` y `approved_at`. | HU-01, HU-02 |
| **RecordsTable** | `record_key` = `node_id#student_id` | Cédula, nombre, programa, estado académico, asignaturas con su estado, `password_hash`, `digital_signature_hash` y fecha de sincronización. | HU-03 |
| **TokensTable** | `jti` (32 caracteres) | Cédula, universidad destino (`aud`), nodo de origen, fechas, `revoked` y `ttl`. | HU-04, HU-05 |

**Ejemplo de un nodo aprobado** (lo que realmente queda; la API Key **no** aparece):
```json
{
  "node_id": "IES-1A2B3C4D", "status": "ACTIVO",
  "nit": "899999063-3", "name": "Universidad Nacional de Colombia",
  "domain": "unal.edu.co", "contact_email": "admisiones@unal.edu.co",
  "api_key_hash": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
  "created_at": "2026-11-09T14:02:11+00:00", "approved_at": "2026-11-09T14:05:40+00:00"
}
```
(El valor de `api_key_hash` es ilustrativo.)

**El campo `ttl` de TokensTable.** Es la fecha de vencimiento del token en segundos. DynamoDB borra solo los registros vencidos (en las horas siguientes). Así la lista negra no crece sin fin: un token vencido ya no sirve de todas formas.

---

## 5. Seguridad: qué se protege y cómo

| Qué | Cómo | Dónde se ve |
|---|---|---|
| **API Key del nodo** | La genera el sistema con 256 bits de azar (`rfha_…`). Se muestra una sola vez. En la tabla solo queda su **SHA-256**. | `/admin`, campo `api_key_hash` |
| **Clave del estudiante** | Nunca se guarda: solo su huella **PBKDF2-SHA256** con sal propia (100 000 vueltas). | `RecordsTable.password_hash` |
| **Historial** | Cada registro lleva una **firma SHA-256** del contenido; si alguien cambia una nota, la firma deja de coincidir. | `digital_signature_hash` |
| **Token del estudiante** | **JWT HS256** de 24 h con destino (`aud`) e identificador (`jti`). | `/portal-estudiante` |
| **Revocación** | El `jti` se marca como revocado; la verificación lo consulta cada vez. | Tabla de autorizaciones |
| **Administrador** | Encabezado `X-Admin-Key` comparado en tiempo constante con `ADMIN_KEY`. Sin `ADMIN_KEY` en el servidor, nadie entra. | `/admin` |
| **Nodo contra nodo** | El dueño de los datos sale de la API Key, no del cuerpo: una universidad no puede escribir datos de otra. | `/panel-nodo` |
| **Mensajes de error** | Cédula inexistente y clave incorrecta dan el mismo mensaje y el mismo costo de cálculo. | `/portal-estudiante` |
| **Navegador** | Política de contenido estricta (sin scripts ni estilos en línea), `nosniff`, sin referrer; las claves viven solo en la memoria de la página. | Todas las pantallas |
| **Abuso** | API Gateway limita a 20 peticiones por segundo (ráfaga de 50). | API Gateway |

---

## 6. Qué hace cada historia de usuario

### HU-01. Registro de universidad (`/registro-nodo`)
La universidad escribe NIT, nombre, dominio y correo. El sistema valida (en el navegador y otra vez en el servidor), rechaza NIT repetidos y crea el nodo en `PENDIENTE_APROBACION` con un código `IES-XXXXXXXX`.
**API:** `POST /api/v1/nodes/register` → `201`, `409` (NIT repetido), `422` (datos inválidos).

### HU-02. Aprobación y API Key (`/admin`)
El administrador escribe su clave, ve las solicitudes y pulsa **Aprobar**. El nodo pasa a `ACTIVO` y aparece la API Key una sola vez.
**API:** `GET /api/v1/admin/nodes` y `POST /api/v1/admin/nodes/{node_id}/approve` → `200`, `403` (sin clave), `404` (no existe), `409` (ya aprobado).

### HU-03. Carga de historiales (`/panel-nodo`)
La universidad pega su API Key y un JSON con hasta 100 estudiantes. El sistema identifica el nodo, valida cada dato, calcula el estado de cada asignatura (aprobada con 3,0 o más), firma el historial y guarda con **upsert** (si el estudiante ya existía, lo reemplaza).
**API:** `POST /api/v1/node/sync-records` → `200` con recibidos/nuevos/actualizados, `403`, `422`.

### HU-04. Autorización del estudiante (`/portal-estudiante`)
El estudiante entra con cédula y clave, elige la universidad y genera un **token de 24 horas** dirigido solo a ella.
**API:** `POST /api/v1/student/auth-token` → `201`, `401`, `404`, `422`. Complemento público: `GET /api/v1/nodes/active`.

### HU-05. Revocación (`/portal-estudiante`)
El estudiante ve sus autorizaciones (activa, revocada o expirada) y revoca las que quiera. Desde ese momento el token ya no es válido.
**API:** `POST /api/v1/student/tokens/list` y `POST /api/v1/student/tokens/{jti}/revoke` → `200`, `401`, `404`.

---

## 7. Pruebas en pantalla, escena por escena

Se hacen **con clics, delante del público**. Cada escena indica los clics, lo que se ve, qué hace el **código (middleware)** y qué hace **AWS**. Úsala en este orden: cada escena prepara la siguiente.

**Antes de empezar** abre las cuatro pantallas en pestañas del navegador y ten a mano la `ADMIN_KEY`. Si es la primera petición del día, tarda unos segundos (arranque en frío): ábrela con unos minutos de anticipación.

**Datos ficticios que se usan:**

| Dato | Valor |
|---|---|
| Universidad | NIT `899999063-3` · «Universidad Nacional de Colombia» · `unal.edu.co` · `admisiones@unal.edu.co` |
| Estudiante 1 | Documento `1012345678` · clave `Clave-2026-A` |
| Estudiante 2 | Documento `1098765432` · clave `Clave-2026-B` |

> Si el NIT ya existe porque se probó antes, usa otro (por ejemplo `860007386`) o limpia los datos (sección 8.4).

### Bloque A. Registro (HU-01)

#### Escena 1. Registro exitoso
- **Clics:** en `/registro-nodo` escribe los datos de la universidad y pulsa **Solicitar registro**.
- **Se ve:** «Solicitud enviada», estado **Pendiente de aprobación** y un código `IES-XXXXXXXX`. Pulsa **Copiar código**.
- **Middleware:** FastAPI valida con las mismas reglas que el navegador, comprueba que el NIT no exista y crea el nodo en `PENDIENTE_APROBACION`.
- **AWS:** API Gateway recibe el `POST` y despierta la Lambda; la Lambda hace un `Scan` y un `PutItem` en **NodesTable**.
- **Conclusión:** entrar a la red empieza con una solicitud, no con acceso inmediato.

#### Escena 2. NIT repetido
- **Clics:** pulsa **Registrar otra institución** y envía el mismo NIT.
- **Se ve:** error bajo el NIT: «Ya existe una solicitud o un nodo con este NIT.»
- **Middleware:** el `Scan` encuentra el NIT y responde `409`; no crea nada.
- **AWS:** solo lectura en NodesTable.
- **Conclusión:** una universidad no puede duplicar su inscripción.

#### Escena 3. Datos inválidos
- **Clics:** escribe `abc` en el NIT y deja un campo vacío; pulsa **Solicitar registro**.
- **Se ve:** un mensaje por campo y el foco en el primero. No se envía nada.
- **Middleware:** la validación del navegador evita la petición; si se saltara, el servidor respondería `422`.
- **AWS:** no interviene (la petición ni sale del navegador).
- **Conclusión:** se valida en dos lugares: el navegador avisa rápido y el servidor no confía en nadie.

### Bloque B. Aprobación (HU-02)

#### Escena 4. Sin la clave de administrador
- **Clics:** en `/admin` escribe una clave cualquiera y pulsa **Cargar solicitudes**.
- **Se ve:** «Clave de administrador incorrecta.»
- **Middleware:** la dependencia `require_admin` compara con `ADMIN_KEY` y corta con `403` antes de tocar la base.
- **AWS:** la Lambda responde sin consultar DynamoDB.
- **Conclusión:** administrar la red exige una clave que solo tiene el administrador.

#### Escena 5. Aprobar una universidad
- **Clics:** escribe la `ADMIN_KEY`, **Cargar solicitudes**, y pulsa **Aprobar** en la fila de la universidad.
- **Se ve:** una tarjeta «Nodo aprobado» con la **API Key** (`rfha_…`). Pulsa **Copiar API Key**. La fila ya no tiene botón y el estado es «Activo».
- **Middleware:** genera la clave con 256 bits de azar, calcula su SHA-256, guarda solo el hash y cambia el estado a `ACTIVO`. Devuelve la clave una sola vez.
- **AWS:** `GetItem` y `UpdateItem` en **NodesTable**. La API Key nunca llega a la base.
- **Conclusión:** aunque alguien viera la base de datos, no podría usar las claves.

#### Escena 6. Aprobar dos veces
- **Clics:** con la API Key ya mostrada, pulsa **Ocultar** y recarga la lista con el filtro **Solo nodos activos**.
- **Se ve:** la universidad aparece sin botón **Aprobar**.
- **Middleware:** si se insistiera por la API, respondería `409` y no cambiaría la clave.
- **AWS:** `Scan` con filtro por estado en NodesTable.
- **Conclusión:** la clave no se puede volver a ver; si se pierde, se emite otra.

### Bloque C. Carga de historiales (HU-03)

#### Escena 7. API Key incorrecta
- **Clics:** en `/panel-nodo` escribe `rfha_incorrecta`, pulsa **Cargar ejemplo** y **Sincronizar historiales**.
- **Se ve:** «API Key incorrecta o nodo no activo.»
- **Middleware:** calcula el SHA-256 de lo escrito, no encuentra ningún nodo con ese hash y responde `403`.
- **AWS:** `Scan` en NodesTable sin resultados; no se escribe nada.
- **Conclusión:** solo una universidad aprobada puede cargar datos.

#### Escena 8. Carga correcta
- **Clics:** pega la API Key de la escena 5, **Cargar ejemplo**, **Sincronizar historiales**.
- **Se ve:** «Recibidos 2 · Nuevos 2 · Actualizados 0».
- **Middleware:** identifica el nodo por la API Key, valida a los dos estudiantes, calcula el estado de cada asignatura, firma cada historial con SHA-256 y guarda solo la huella de la clave.
- **AWS:** por cada estudiante, `GetItem` y `PutItem` en **RecordsTable**; las notas se guardan como números decimales.
- **Conclusión:** los datos quedan en el nodo de la universidad y firmados.

#### Escena 9. Repetir la carga (upsert)
- **Clics:** pulsa **Sincronizar historiales** otra vez.
- **Se ve:** «Nuevos 0 · Actualizados 2».
- **Middleware:** encuentra la clave `node_id#student_id` y reemplaza; no duplica.
- **AWS:** `PutItem` sobre la misma clave.
- **Conclusión:** la sincronización se puede repetir sin miedo.

#### Escena 10. Dato inválido
- **Clics:** en el JSON cambia una nota a `7` y sincroniza.
- **Se ve:** error indicando el campo, por ejemplo «records › 0 › courses › 0 › grade».
- **Middleware:** responde `422` y **no guarda ninguno** de los estudiantes del lote.
- **AWS:** ninguna escritura.
- **Conclusión:** un lote con un error no deja datos a medias.

### Bloque D. Permiso del estudiante (HU-04 y HU-05)

#### Escena 11. Clave incorrecta
- **Clics:** en `/portal-estudiante` escribe documento `1012345678` y clave `equivocada`; pulsa **Ingresar**.
- **Se ve:** «Cédula o clave incorrecta.» Prueba también con un documento que no existe: **el mensaje es el mismo**.
- **Middleware:** compara contra la huella PBKDF2 y responde `401`; con una cédula inexistente hace el mismo cálculo para que ni el mensaje ni el tiempo delaten si existe.
- **AWS:** `Scan` por cédula en RecordsTable.
- **Conclusión:** el sistema no revela qué estudiantes existen.

#### Escena 12. Generar la autorización
- **Clics:** ingresa con `1012345678` / `Clave-2026-A`, elige la universidad y pulsa **Generar autorización**.
- **Se ve:** un token (tres partes separadas por puntos), la universidad autorizada y su vencimiento (24 horas). **Copiar token**. Abajo, la fila «Activo».
- **Middleware:** comprueba la clave, comprueba que la universidad destino exista y esté activa, crea un JWT con `sub`, `doc`, `origin`, `aud`, `jti`, `iat` y `exp`, y registra el token.
- **AWS:** `GetItem` en NodesTable (destino) y `PutItem` en **TokensTable** con su `ttl`.
- **Conclusión:** el estudiante decide a quién y por cuánto tiempo.

#### Escena 13. Revocar
- **Clics:** genera una segunda autorización y pulsa **Revocar** en la primera.
- **Se ve:** la primera fila pasa a «Revocado» y pierde el botón; la segunda sigue «Activo».
- **Middleware:** verifica que el token sea de esa persona y marca su `jti` como revocado. La función `verify_token`, que usarán HU-06 y HU-07, rechazará ese token aunque su firma y su fecha sigan siendo buenas.
- **AWS:** `GetItem` y `UpdateItem` (`revoked = true`) en **TokensTable**.
- **Conclusión:** el permiso se puede retirar al instante, sin esperar las 24 horas.

#### Escena 14. Salir
- **Clics:** pulsa **Salir**.
- **Se ve:** vuelve el formulario de ingreso y se borran la clave y el token de la pantalla.
- **Middleware:** no hay sesión en el servidor que cerrar: la página olvida las credenciales.
- **AWS:** no interviene.
- **Conclusión:** nada queda guardado en el navegador.

### Resumen

| Escena | Pantalla | Resultado | Quién decide |
|---|---|---|---|
| 1. Registro | `/registro-nodo` | 201, `PENDIENTE_APROBACION` | Código + NodesTable |
| 2. NIT repetido | `/registro-nodo` | 409 | Código |
| 3. Datos inválidos | `/registro-nodo` | Aviso en pantalla (422 si llegara) | Navegador y código |
| 4. Sin clave de administrador | `/admin` | 403 | Código |
| 5. Aprobar | `/admin` | 200 + API Key única vez | Código + NodesTable |
| 6. Aprobar otra vez | `/admin` | 409 (por API) | Código |
| 7. API Key incorrecta | `/panel-nodo` | 403 | Código |
| 8. Carga | `/panel-nodo` | 200, 2 nuevos | Código + RecordsTable |
| 9. Repetir | `/panel-nodo` | 200, 2 actualizados | Código |
| 10. Dato inválido | `/panel-nodo` | 422, nada guardado | Código |
| 11. Clave incorrecta | `/portal-estudiante` | 401 | Código |
| 12. Autorizar | `/portal-estudiante` | 201 + token | Código + TokensTable |
| 13. Revocar | `/portal-estudiante` | 200, estado «Revocado» | Código + TokensTable |
| 14. Salir | `/portal-estudiante` | Se borran las credenciales | Navegador |

---

## 8. Desplegar, actualizar, limpiar y borrar

Requiere el AWS CLI, Python 3.12 y la sesión iniciada (`aws login --region us-east-2 --profile rfha`). El archivo `.env` debe tener `JWT_SECRET` y `ADMIN_KEY` (la primera vez, `run-app.cmd` los crea).

### 8.1 Desplegar o actualizar
```powershell
.\.venv\Scripts\python.exe scripts\deploy_aws.py app --profile rfha --region us-east-2
```
Arma el paquete, lo sube a S3, crea o actualiza el stack `rfha-app` y al final imprime `LISTO. Dirección pública: …`. La dirección **no cambia** al actualizar. Tarda de 2 a 4 minutos.

### 8.2 Comprobar que quedó bien
```powershell
.\.venv\Scripts\python.exe scripts\smoke_aws.py app https://ypybm0azfg.execute-api.us-east-2.amazonaws.com
```
Hace el recorrido completo (registro, aprobación, carga, token, revocación) y muestra `[OK]` por paso. **Deja datos de prueba** en las tablas (una universidad «Universidad de Prueba Humo»).

### 8.3 Ver los registros si algo falla
```powershell
aws logs tail /aws/lambda/rfha-app --since 15m --profile rfha --region us-east-2
```

### 8.4 Limpiar los datos de prueba antes de exponer
```powershell
.\.venv\Scripts\python.exe scripts\clean_aws_data.py --profile rfha --region us-east-2          # solo cuenta
.\.venv\Scripts\python.exe scripts\clean_aws_data.py --profile rfha --region us-east-2 --yes    # borra
```
Vacía las tres tablas sin borrar el stack.

### 8.5 Borrar todo al terminar
```powershell
.\.venv\Scripts\python.exe scripts\deploy_aws.py app --delete --profile rfha --region us-east-2
```
Borra la API, la Lambda, las tres tablas y los registros. Los datos no se pueden recuperar.

### 8.6 Rotar la clave de administrador
Cambia `ADMIN_KEY` en `.env` y vuelve a desplegar (8.1). Las API Keys de los nodos **no** cambian.

---

## 9. Plan A (local) y Plan B (AWS)

| | Plan A: tu computador | Plan B: AWS |
|---|---|---|
| Cómo se levanta | `.\run-app.cmd` (macOS/Linux: `bash run-demo.sh --app`) | `deploy_aws.py app` |
| Dirección | http://127.0.0.1:8001 | La de la sección 1 |
| Dónde viven los datos | En la memoria del programa: **se pierden al detenerlo**. | En DynamoDB: persisten. |
| Clave de administrador | La imprime `run-app.cmd` al arrancar (viene de `.env`). | La de `.env` de quien desplegó. |
| Internet | No hace falta. | Hace falta. |
| Cuándo usarlo | Ensayar, programar y como respaldo. | Exponer y mostrar la nube real. |

Ambos corren **el mismo código**; lo único que cambia es `REPOSITORY_BACKEND` (`memory` o `dynamodb`).

---

## 10. Problemas frecuentes

| Qué ves | Causa probable | Qué hacer |
|---|---|---|
| La primera pantalla tarda varios segundos | Arranque en frío de la Lambda. | Abrir la pantalla unos minutos antes de exponer. |
| «Clave de administrador incorrecta» con la clave correcta | Se redesplegó con otra `ADMIN_KEY` o hay espacios al copiar. | Revisar `.env`, volver a desplegar y pegar sin espacios. |
| «Ya existe una solicitud o un nodo con este NIT» | Se probó antes. | Usar otro NIT o limpiar los datos (8.4). |
| «API Key incorrecta o nodo no activo» | Clave mal copiada, o el nodo no se aprobó. | Aprobar en `/admin`; si se perdió la clave, registrar otro nodo (no se recupera). |
| «Cédula o clave incorrecta» | Aún no se cargó el historial, o la clave no coincide. | Hacer la escena 8 y usar `Clave-2026-A`. |
| La lista de universidades del portal está vacía | No hay nodos activos. | Aprobar una universidad (escena 5). |
| Error de red en el formulario | Sin internet o servidor apagado. | Los datos escritos se conservan; reintentar. |
| `403` con `Missing Authentication Token` | Dirección mal escrita. | Usar las rutas de la sección 1. |
| Todo vacío después de reiniciar (local) | Los datos locales viven en memoria. | Es lo esperado; repetir las escenas 1, 5 y 8. |

---

## 11. Preguntas probables

**¿Por qué no hay una base de datos por universidad?** Por costo y simplicidad se simula con una tabla donde cada historial lleva el `node_id` de su universidad. La separación lógica es real: cada nodo solo escribe lo suyo. La réplica llega con HU-08.

**¿Qué pasa si alguien roba la base de datos?** No encuentra API Keys (solo hashes SHA-256 de claves aleatorias) ni claves de estudiantes (solo hashes PBKDF2 con sal). Sí vería los historiales, por eso están cifrados en reposo por DynamoDB y los datos de la demo son ficticios.

**¿Por qué el token lleva destino (`aud`)?** Para que sirva solo a la universidad que el estudiante eligió. Si otra universidad lo usa, se rechaza.

**¿Cómo se revoca un JWT si es autocontenido?** Cada token lleva un `jti` y se registra en `TokensTable`. Revocar marca ese registro y la verificación lo consulta cada vez.

**¿Por qué una sola Lambda?** Menos piezas, mismo resultado, y escala igual: AWS crea más copias si hay más peticiones (transparencia de escalado).

**¿Cuánto cuesta?** En el plan Free de AWS, nada: Lambda, API Gateway y DynamoDB bajo demanda consumen una fracción de los créditos con este volumen. Se vigila en **Billing**.

**¿Dónde está la consulta del historial?** En HU-06 y HU-07. El mecanismo del permiso ya está completo aquí (`src/app/tokens.py::verify_token`) y la demo (`docs/DEMO.md`) muestra cómo se comporta el middleware al consultar.
