# RFHA-IES — Red Federada de Historiales Académicos

> Sistema distribuido de intercambio federado de historiales académicos interuniversitarios, desplegado como serverless en AWS.

**URL pública:** `https://ypybm0azfg.execute-api.us-east-2.amazonaws.com`  
**Rama activa:** `dev` → PR hacia `main`  
**Stack:** Python 3.12 · FastAPI · AWS Lambda + API Gateway · DynamoDB · Mangum

---

## Tabla de módulos

| Módulo web | URL | Descripción |
|------------|-----|-------------|
| Inicio | `/` | Menú principal |
| Registro de universidad | `/registro-nodo` | HU-01 |
| Administración | `/admin` | HU-02 |
| Panel del nodo | `/panel-nodo` | HU-03 |
| Portal del estudiante | `/portal-estudiante` | HU-04 / HU-05 |
| Consulta federada | `/consulta` | HU-06 / HU-07 / HU-08 |
| Bitácora de auditoría | `/auditoria` | HU-09 |
| Reportes ejecutivos | `/reportes` | PDF por tipo de reporte |

---

## 1. Arquitectura general

```mermaid
flowchart TD
    subgraph Nodos["Nodos IES (universidades)"]
        N1[Universidad A\nPanel del nodo]
        N2[Universidad B\nPanel del nodo]
    end

    subgraph Middleware["Middleware RFHA-IES\n(AWS Lambda + API Gateway)"]
        GW[API Gateway\nus-east-2]
        LM[AWS Lambda\nFastAPI + Mangum]
        DB[(DynamoDB\n5 tablas)]
    end

    subgraph Actores["Actores externos"]
        STU[Estudiante\nPortal web]
        ADM[Administrador\nPanel /admin]
    end

    N1 -->|"POST /api/v1/node/sync-records<br>X-Node-API-Key"| GW
    N2 -->|"GET /api/v1/federated/academic-history/{id}<br>X-Student-Consent-Token"| GW
    STU -->|"POST /api/v1/students/token<br>Credenciales + nodo destino"| GW
    ADM -->|"PATCH /api/v1/admin/nodes/{id}/approve<br>X-Admin-Key"| GW

    GW --> LM
    LM --> DB
```

### Flujo completo de una petición

```mermaid
sequenceDiagram
    actor U as Universidad B (consulta)
    participant GW as API Gateway
    participant LM as Lambda (FastAPI)
    participant DB as DynamoDB

    U->>GW: GET /api/v1/federated/academic-history/{student_id} (Headers: X-Node-API-Key, X-Student-Consent-Token)
    GW->>LM: invoca handler (Mangum adapta ASGI→Lambda)
    LM->>DB: find_by_api_key_hash(sha256(api_key)) → NodesTable
    DB-->>LM: nodo ACTIVO confirmado
    LM->>LM: verify_token(jwt, audience=node_id, tokens_repo)\n  → valida firma HS256, exp, aud, lista negra
    LM->>DB: records.get(origin_node, student_id) → RecordsTable
    alt Nodo origen caído (HU-08)
        DB-->>LM: None / excepción
        LM->>DB: replicas.get(origin_node, student_id) → ReplicasTable
        DB-->>LM: ítem de réplica
        LM->>LM: X-Data-Source: Replica
    else Nodo origen disponible
        DB-->>LM: ítem primario
        LM->>LM: X-Data-Source: Primary
    end
    LM->>LM: record_signature(signed_fields) == digital_signature_hash ?
    LM->>DB: audits.record_log({...}) → AuditLogsTable (inmutable)
    LM-->>GW: 200 JSON + X-Data-Source header
    GW-->>U: respuesta cifrada TLS
```

---

## 2. Fundamentos teóricos aplicados al código

### 2.1 ¿Qué es el Middleware y por qué RFHA-IES lo es?

Un **middleware** es una capa de software que actúa como intermediario entre sistemas heterogéneos: recibe mensajes, los valida, transforma o enruta, y los entrega al destino correcto — sin que los extremos se conozcan directamente.

RFHA-IES cumple exactamente este rol:

| Función de middleware | Dónde ocurre en el código |
|-----------------------|---------------------------|
| **Interceptación** de cada petición | `src/app/security.py` → `require_node()` y `require_admin()` validan la identidad antes de que el router procese nada |
| **Transformación** de datos | `src/app/routers/federated.py` → `_plain()` convierte `Decimal` de DynamoDB a tipos JSON; `_summary()` agrega GPA y créditos |
| **Enrutamiento federado** | `federated.py` → decide entre `records` (primario) y `replicas` (réplica) según el estado del nodo origen |
| **Verificación de integridad** | `security.py` → `record_signature()` recalcula SHA-256 del JSON canónico y compara con `digital_signature_hash` |
| **Bitácora transversal** | `federated.py` → `_log()` escribe en `AuditLogsTable` en cada rama del flujo (éxito, denegado, error) |

### 2.2 Sistema distribuido vs. centralizado

RFHA-IES es un **sistema distribuido federado**, no un monolito, por las siguientes evidencias en el código:

| Propiedad SD | Evidencia en el código |
|---|---|
| **Nodos autónomos con identidad propia** | Cada universidad recibe una API Key única (`security.py → new_api_key()`) cuyo hash SHA-256 se guarda en `NodesTable`. El nodo **nunca** puede escribir datos de otro: `sync.py` L.40 → `"node_id": node["node_id"]` viene de la API Key autenticada, no del body. |
| **Particionamiento de datos** | `repositories.py → record_key()` L.152: `f"{node_id}#{student_id}"` — cada registro está segmentado por nodo. Un nodo no puede acceder a registros ajenos. |
| **Comunicación por red con protocolo** | Todo intercambio es HTTP REST con cabeceras de autenticación (`X-Node-API-Key`, `X-Student-Consent-Token`, `X-Admin-Key`). |
| **Ausencia de estado local compartido** | Lambda es stateless: cada invocación es independiente. El estado está exclusivamente en DynamoDB. |
| **Tolerancia a particiones (CAP)** | `federated.py` L.100-114: si el nodo origen falla, se activa failover automático a `ReplicasTable` (modelo AP). |
| **Service Registry** | `nodes.py → GET /api/v1/nodes/active`: devuelve los nodos disponibles — equivalente a Eureka/Consul. |
| **Autorización delegada** | El estudiante emite un JWT con `aud` = ID del nodo destino (`tokens.py`). Un token para Universidad A no sirve para Universidad B (`verify_token` lanza `InvalidAudienceError`). |

### 2.3 Teorema CAP

RFHA-IES es un sistema **AP** (Available + Partition-tolerant):

- **Disponibilidad:** ante fallo del nodo primario, la réplica responde (L.111-114 `federated.py`).
- **Tolerancia a particiones:** el middleware sigue operando aunque un nodo IES esté caído.
- **Consistencia eventual:** la réplica puede estar ligeramente detrás del primario; es la última versión sincronizada (`sync.py` L.57-58: `records.upsert()` → `replicas.upsert()` en el mismo request).

---

## 3. Infraestructura AWS — Mapeo código↔nube

| Servicio AWS | Rol | Configuración | Archivo relevante |
|---|---|---|---|
| **AWS Lambda** | Ejecuta la app FastAPI (serverless) | Runtime Python 3.12, timeout configurable en SAM template | `src/app/main.py` L.58 → `handler = Mangum(app, lifespan="off")` |
| **API Gateway (HTTP API)** | Punto de entrada único; enruta al Lambda | Integración proxy (`/{proxy+}`) | `template.yaml` (generado por `scripts/deploy_aws.py`) |
| **DynamoDB** | Persistencia NoSQL distribuida | 5 tablas, capacidad on-demand, AES-256 en reposo | `src/app/repositories.py` → clases `Dynamo*Repository` |
| **S3** | Almacenamiento del paquete Lambda antes del deploy | Bucket temporal durante `sam package` | `scripts/deploy_aws.py` |
| **CloudFormation / SAM** | IaC: define Lambda + API GW + permisos IAM | Stack `rfha-app` en `us-east-2` | `scripts/deploy_aws.py` |
| **IAM** | Rol de ejecución del Lambda con permisos DynamoDB | Generado automáticamente por SAM | `template.yaml` |

### ¿Por qué DynamoDB y no RDS/PostgreSQL?

| Criterio | DynamoDB | RDS |
|---|---|---|
| Escalado | Automático (on-demand), sin gestión de servidores | Requiere provisionar instancias |
| Latencia baja | Acceso por clave de partición en < 10 ms | Depende del tamaño de la query |
| TTL nativo | Elimina tokens vencidos automáticamente (`ttl` = exp del JWT) | Requiere job periódico |
| Modelo de acceso | Por clave (`node_id#student_id`), sin JOINs | Relacional, óptimo para JOINs |
| Sin estado de conexión | Perfecto para Lambda (no mantiene conexión persistente) | Connection pooling necesario |

El esquema de acceso del proyecto (siempre por `node_id` + `student_id`) es exactamente el caso de uso ideal de DynamoDB.

---

## 4. Persistencia y base de datos

### Tablas DynamoDB

| Tabla | Clave de partición | Propósito | Clase repositorio |
|---|---|---|---|
| `NodesTable` | `node_id` (IES-XXXXXXXX) | Nodos institucionales y hash de API Key | `DynamoNodeRepository` |
| `RecordsTable` | `record_key` (`node_id#student_id`) | Historiales académicos (primario) | `DynamoRecordRepository` |
| `ReplicasTable` | `record_key` | Copia de réplica para failover (HU-08) | `DynamoRecordRepository` (misma clase, tabla distinta) |
| `TokensTable` | `jti` (UUID hex) | Tokens activos del estudiante + lista negra | `DynamoTokenRepository` |
| `AuditLogsTable` | `log_id` (AUDIT-XXXXXXXXXXXX) | Bitácora inmutable (solo PutItem) | `DynamoAuditRepository` |

### Patrón de acceso clave

```python
# repositories.py L.152
def record_key(node_id: str, student_id: str) -> str:
    return f"{node_id}#{student_id}"
```

Esto garantiza que el Scan de DynamoDB por `document_number` (`find_by_document`) siempre opera dentro del espacio de claves de un nodo, y que el `upsert` por `record_key` sea idempotente (carga repetida = actualización).

### Neguentropía mediante TTL

```python
# repositories.py L.235 (DynamoTokenRepository)
# El atributo `ttl` (= exp del token) hace que DynamoDB borre el registro al vencer.
```

El atributo `ttl` = Unix timestamp de expiración del JWT. DynamoDB lo elimina automáticamente dentro de las 48 h posteriores al vencimiento, manteniendo la tabla limpia sin ningún job de limpieza — esto es **neguentropía aplicada** (el sistema expulsa "ruido" de forma autónoma).

---

## 5. Seguridad: cifrado y mecanismos de protección

### Capas de cifrado

| Capa | Mecanismo | Código |
|---|---|---|
| **En tránsito** | TLS 1.2+ forzado por API Gateway (AWS gestiona el certificado) | Transparente en infraestructura |
| **API Key del nodo** | SHA-256 (nunca se guarda en texto plano) | `security.py → hash_api_key()` L.23-24 |
| **Contraseña del estudiante** | PBKDF2-HMAC-SHA256, 100.000 iteraciones, sal de 16 bytes aleatoria | `security.py → hash_password()` L.29-32 |
| **Firma del historial** | SHA-256 del JSON canónico (sort_keys, sin espacios) | `security.py → record_signature()` L.55-57 |
| **Token de consentimiento** | JWT HS256 con `jti`, `aud`, `exp` y lista negra en DynamoDB | `tokens.py → issue_token()` / `verify_token()` |
| **En reposo (DynamoDB)** | AES-256 gestionado por AWS KMS (activado por defecto) | Configuración de infraestructura AWS |
| **Timing-safe comparisons** | `hmac.compare_digest()` para Admin Key y contraseñas | `security.py` L.44-47, L.65 |

### CSP (Content Security Policy)

```python
# main.py L.12-18
PAGE_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; "
        "base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    ),
    ...
}
```

Todos los scripts son externos (`type="module"`) para cumplir con `script-src 'self'`. No hay inline scripts ni inline styles.

---

## 6. Alta disponibilidad y tolerancia a fallos

### ¿Por qué el sistema no se cae?

| Mecanismo | Detalle |
|---|---|
| **Escalado automático de Lambda** | AWS instancia múltiples ejecuciones concurrentes en milisegundos ante picos de carga. No hay servidor que administrar. SLA: 99.95%. |
| **Failover a réplica (HU-08)** | `federated.py` L.100-114: si `records.get()` retorna `None` o lanza excepción, se consulta `ReplicasTable` automáticamente. La cabecera `X-Data-Source: Replica` lo evidencia. |
| **Simulación de caída** | La cabecera `X-Simulate-Down: true` (o la variable `SIMULATE_NODE_DOWN` en `.env`) fuerza el failover sin necesidad de apagar nada. |
| **Idempotencia del upsert** | Si una sincronización falla a mitad, se puede re-ejecutar sin duplicar datos: `put_item` sobreescribe por `record_key`. |
| **Tokens con expiración** | TTL de 24 h evita acumulación de tokens activos. La lista negra permite revocación inmediata. |
| **Bitácora inmutable** | `AuditLogsTable` solo recibe `PutItem` (nunca `UpdateItem` ni `DeleteItem`). Cualquier operación queda trazada con IP, resultado y fuente de datos. |

---

## 7. Ejecución local

```bash
# 1. Crear entorno y arrancar
python scripts/run_demo.py --app --port 8001

# 2. Tests completos
.venv/Scripts/pytest -q

# 3. Deploy a AWS
python scripts/deploy_aws.py app --profile rfha --region us-east-2
```

### Variables de entorno (`.env`)

| Variable | Descripción | Default |
|---|---|---|
| `REPOSITORY_BACKEND` | `memory` (local) o `dynamodb` (AWS) | `memory` |
| `ADMIN_KEY` | Clave del administrador general | — |
| `JWT_SECRET` | Secreto de firma de tokens | valor de desarrollo |
| `SIMULATE_NODE_DOWN` | `node_id` de nodo a simular caído | — |
| `NODES_TABLE` | Nombre de la tabla DynamoDB | `NodesTable` |
| `RECORDS_TABLE` | — | `RecordsTable` |
| `REPLICAS_TABLE` | — | `ReplicasTable` |
| `TOKENS_TABLE` | — | `TokensTable` |
| `AUDIT_TABLE` | — | `AuditLogsTable` |

---

## 8. Historias de usuario implementadas

| HU | Descripción | Router / archivo principal |
|----|-------------|---------------------------|
| HU-01 | Registro de universidad como nodo | `routers/nodes.py → POST /api/v1/nodes/register` |
| HU-02 | Aprobación de nodo por administrador | `routers/admin.py → POST /api/v1/admin/nodes/{id}/approve` |
| HU-03 | Sincronización de historiales | `routers/sync.py → POST /api/v1/node/sync-records` |
| HU-04 | Emisión de token de consentimiento | `routers/students.py → POST /api/v1/students/token` |
| HU-05 | Revocación de token | `routers/students.py → DELETE /api/v1/students/token/{jti}` |
| HU-06 | Consulta federada con token | `routers/federated.py → GET /api/v1/federated/academic-history/{id}` |
| HU-07 | Bloqueo por token inválido / revocado | mismo endpoint, control L.86-94 |
| HU-08 | Tolerancia a fallos + conmutación a réplica | mismo endpoint, control L.100-114 |
| HU-09 | Bitácora inmutable de auditoría + filtro `since` | `routers/audit.py` + `_log()` en `federated.py` |
| HU-10 | Interfaz web completa | `main.py PAGES` + `static/` |
| SD-01 | Control de concurrencia optimista (ConditionExpression) | `repositories.py → DynamoRecordRepository.upsert()` |
| SD-04 | Estado de salud de nodos (ACTIVO/DEGRADADO) | `routers/admin.py → PATCH /api/v1/admin/nodes/{id}/status` |

---

## 9. Bucles de retroalimentación (TGS)

```mermaid
flowchart LR
    A[Universidad solicita registro] --> B[Admin aprueba/rechaza]
    B --> C{Estado del nodo}
    C -->|ACTIVO| D[Nodo puede sincronizar y ser consultado]
    C -->|RECHAZADO| E[Nodo inactivo - sin acceso]

    F[Estudiante emite token] --> G[Universidad consulta historial]
    G --> H[Bitácora registra IP y resultado]
    H --> I[Estudiante puede revocar si detecta abuso]
    I --> F
```

Los tres loops de feedback del sistema:
1. **Aprobación:** Solicitud → Revisión admin → Estado nodo → Capacidad de operación.
2. **Consentimiento:** Emisión de token → Consulta → Auditoría → Revocación si necesario.
3. **Integridad:** Sincronización firma SHA-256 → Consulta verifica firma → Error 500 si no coincide → Nodo debe re-sincronizar.

---

## 10. Estructura del repositorio

```
src/
├── app/
│   ├── config.py          # Variables de entorno
│   ├── main.py            # FastAPI app + páginas HTML + handler Lambda
│   ├── models.py          # Pydantic models (validación de entrada)
│   ├── repositories.py    # Acceso a DynamoDB (Protocol + In-Memory + Dynamo)
│   │                        # → DynamoRecordRepository.upsert: ConditionExpression SD-01
│   ├── security.py        # SHA-256, PBKDF2, firma, control de acceso
│   ├── tokens.py          # JWT HS256: emisión y verificación
│   ├── reports.py         # Generación de PDF con ReportLab
│   ├── routers/
│   │   ├── admin.py       # HU-02 + PATCH /nodes/{id}/status (SD-04)
│   │   ├── audit.py       # HU-09: bitácora + ?since (B5) + no-cache
│   │   ├── federated.py   # HU-06/07/08: consulta federada
│   │   ├── nodes.py       # HU-01: registro
│   │   ├── students.py    # HU-04/05: tokens
│   │   └── sync.py        # HU-03: sincronización + manejo 409 SD-01
│   └── static/            # HTML + CSS + JS (sin framework de build)
scripts/
├── deploy_aws.py          # SAM build + package + deploy
└── run_demo.py            # Entorno local con venv automático
tests/                     # suite pytest
```

---

## 11. Diagramas TGS — DFD Nivel 0 y Nivel 1 (TGS-01)

### DFD Nivel 0 — Vista del sistema completo

```mermaid
flowchart LR
    UNI([Universidad\nNodo IES])
    STU([Estudiante])
    ADM([Administrador])
    SYS[RFHA-IES\nMiddleware]

    UNI -->|Historiales académicos| SYS
    STU -->|Consentimiento / Token| SYS
    ADM -->|Aprobaciones / Configuración| SYS
    SYS -->|Historial verificado + auditoría| UNI
    SYS -->|Estado de tokens activos| STU
    SYS -->|Reportes + logs de red| ADM
```

### DFD Nivel 1 — Procesos internos del Middleware

```mermaid
flowchart TD
    P1["P1\nAutenticación\nde Nodo\nsecurity.py"]
    P2["P2\nValidación JWT\ntokens.py"]
    P3["P3\nEnrutamiento\nFederado\nfederated.py"]
    P4["P4\nFailover\nRéplica\nfederated.py"]
    P5["P5\nVerificación\nIntegridad SHA-256\nsecurity.py"]
    P6["P6\nAuditoría\nInmutable\nrepositories.py"]

    DS1[(NodesTable)]
    DS2[(TokensTable)]
    DS3[(RecordsTable)]
    DS4[(ReplicasTable)]
    DS5[(AuditLogsTable)]

    REQ([Petición\nde consulta]) --> P1
    P1 --> DS1
    DS1 --> P1
    P1 --> P2
    P2 --> DS2
    DS2 --> P2
    P2 --> P3
    P3 --> DS3
    DS3 --> P3
    P3 -->|Nodo caído| P4
    P4 --> DS4
    DS4 --> P4
    P4 --> P5
    P3 --> P5
    P5 --> P6
    P6 --> DS5
    P5 --> RESP([Respuesta\nverificada])
```

---

## 12. Sistema abierto y propiedades TGS (TGS-02)

| Propiedad TGS | Implementación en RFHA-IES |
|---|---|
| **Sistema abierto** | Interactúa con el entorno (universidades, estudiantes, admin) a través de API REST (frontera definida: HTTP + TLS) |
| **Subsistemas** | Nodo de registro (`nodes.py`), gestión admin (`admin.py`), historial (`sync.py`), autenticación (`students.py`), auditoría (`audit.py`), consulta federada (`federated.py`) |
| **Equifinalidad** | Múltiples rutas al mismo resultado: consulta exitosa vía nodo primario (`RecordsTable`) o vía réplica (`ReplicasTable`) — mismo JSON de respuesta, distinto `X-Data-Source` |
| **Homeostasis** | El sistema mantiene consistencia ante fallos gracias al failover automático (`federated.py` L.100-114) y la lista negra de tokens (`TokensTable.revoked=True`) |
| **Neguentropía** | (1) Firmas SHA-256 detectan corrupción → `record_signature()`. (2) Bitácora inmutable preserva historia → solo `PutItem` en `AuditLogsTable`. (3) TTL automático en `TokensTable` elimina tokens vencidos. (4) `ConditionExpression` en `DynamoRecordRepository.upsert()` evita escrituras conflictivas. |
| **Retroalimentación** | Loop de aprobación, loop de consentimiento/revocación, loop de integridad (ver §9) |
| **Bucles de feedback** | Ver §9 — cada loop tiene evidencia directa en el código con archivo y línea |

---

## 13. Decisiones Arquitectónicas y Trade-offs

| Decisión | Alternativa | Justificación técnica |
|---|---|---|
| **DynamoDB on-demand** | RDS PostgreSQL | Sin gestión de servidores; TTL nativo para tokens; latencia < 10 ms por clave; ideal para Lambda stateless |
| **JWT HS256 (simétrico)** | RS256 (asimétrico) | Menor overhead computacional; en este modelo el middleware es la única parte que emite y verifica tokens. RS256 sería necesario si los nodos verificaran tokens directamente. |
| **Replicación síncrona** | DynamoDB Streams + SQS | Simple y verificable. La desventaja: si `replicas.upsert()` falla, la réplica queda desactualizada silenciosamente. Para producción: DynamoDB Streams desacoplaría la replicación sin riesgo de fallo síncrono. |
| **API Key en header** | OAuth2 Client Credentials | Más simple de implementar y demostrar; OAuth2 agrega un Authorization Server que escapa al alcance del proyecto académico. |
| **ADMIN_KEY estática** | AWS Secrets Manager | Rotación manual. Para producción se usaría Secrets Manager con rotación automática y Lambda extension para cachear la clave sin consultar el API en cada request. |
| **Cifrado de campo** | AES-256 en reposo (AWS KMS, default) | El campo `doc` (cédula) viaja en el payload JWT sin cifrar (solo firmado). En producción se reemplazaría por JWE (JSON Web Encryption) o se usaría un hash del documento como identificador público. |
| **Concurrencia optimista** | Bloqueo pesimista (mutex) | Lambda es stateless — no puede mantener bloqueos entre invocaciones. `ConditionExpression` en DynamoDB es el mecanismo nativo para control de concurrencia sin locks distribuidos. |


---

## 14. Guía Detallada de Módulos (Backend y Frontend)

Esta sección desglosa minuciosamente cada uno de los componentes de software desarrollados en el proyecto, explicando su rol funcional, su procesamiento interno y sus contratos de entrada/salida.

### 14.1 Backend (`src/app/`)

#### 1. Configuración Global (`src/app/config.py`)
* **Ubicación exacta:** `src/app/config.py`
* **Propósito funcional:** Cargar y centralizar las variables de entorno operativas (credenciales maestras, nombres de tablas DynamoDB, secreto JWT y banderas de simulación de fallos).
* **Funcionamiento interno:** Dispone de la función `load_dotenv()` que lee el archivo `.env` en entorno local sin sobreescribir variables ya inyectadas por el entorno de AWS Lambda. Expone constantes como `REPOSITORY_BACKEND` (`memory` o `dynamodb`), `ADMIN_KEY`, `JWT_SECRET`, `TOKEN_TTL_SECONDS` y nombres de tablas.
* **Entradas y Salidas:** Entradas: variables del sistema o archivo `.env`. Salidas: constantes inmutables para el resto de la aplicación.

#### 2. Orquestador Principal y Enrutamiento Web (`src/app/main.py`)
* **Ubicación exacta:** `src/app/main.py`
* **Propósito funcional:** Instanciar la aplicación FastAPI, configurar las cabeceras de seguridad CSP (Content Security Policy), servir las páginas HTML estáticas y proporcionar el handler serverless compatible con AWS Lambda.
* **Funcionamiento interno:** 
  1. Instancia `app = FastAPI(...)`.
  2. Incluye los 6 routers modulares (`nodes`, `admin`, `sync`, `students`, `federated`, `audit`).
  3. Monta `/static` mediante `StaticFiles`.
  4. Mapea rutas GET de frontend (`/`, `/registro-nodo`, `/admin`, etc.) hacia archivos `.html` aplicando cabeceras estrictas `PAGE_HEADERS` (CSP sin scripts inline).
  5. Instancia `handler = Mangum(app, lifespan="off")` para adaptar eventos ASGI de API Gateway a Lambda.
* **Entradas y Salidas:** Entradas: eventos HTTP/API Gateway v2. Salidas: respuestas HTTP/JSON y streaming de archivos estáticos.

#### 3. Seguridad y Criptografía (`src/app/security.py`)
* **Ubicación exacta:** `src/app/security.py`
* **Propósito funcional:** Gestión criptográfica de API Keys de nodos, contraseñas de estudiantes, firmas de integridad de registros y dependencias de autorización para FastAPI.
* **Funcionamiento interno:**
  * `new_api_key()`: Genera llaves pseudoaleatorias criptográficamente seguras con prefijo `rfha_` usando `secrets.token_urlsafe(32)`.
  * `hash_api_key()`: Calcula hash SHA-256 para almacenamiento seguro de las API Keys.
  * `hash_password()` y `verify_password()`: Implementa PBKDF2-HMAC-SHA256 con 100,000 iteraciones y sal aleatoria de 16 bytes. Usa `DUMMY_HASH` para prevenir ataques de temporización (*timing attacks*) cuando un estudiante no existe.
  * `record_signature()`: Serializa el historial en JSON canónico ordenado (`sort_keys=True`, sin espacios) y genera hash SHA-256 inmutable.
  * `require_admin()` y `require_node()`: Callbacks inyectables en rutas (`Depends`) para validar cabeceras `X-Admin-Key` y `X-Node-API-Key`.
* **Entradas y Salidas:** Entradas: contraseñas, diccionarios de historiales, cabeceras HTTP. Salidas: hashes hexadecimales, booleano de verificación o el diccionario del nodo activo autenticado.

#### 4. Motor de Tokens y Consentimiento Delegado (`src/app/tokens.py`)
* **Ubicación exacta:** `src/app/tokens.py`
* **Propósito funcional:** Emisión y validación criptográfica de tokens JWT de consentimiento estudiantil (`student_auth_token`), control de vigencia y lista negra distribuida.
* **Funcionamiento interno:**
  * `issue_token()`: Construye claims (`sub`=estudiante, `doc`=cédula, `origin`=nodo emisor, `aud`=nodo autorizado, `jti`=identificador único, `iat`, `exp`). Firma con HMAC-SHA256 (`HS256`) y persiste el metadato en `TokensTable` con `revoked=False` y atributo `ttl`.
  * `verify_token()`: Decodifica y valida firma, expiración y audiencia requerida. Consulta `TokensTable` para verificar que `revoked` no sea `True`. Lanza `TokenError` descriptivo si falla alguna regla.
* **Entradas y Salidas:** Entradas: datos del estudiante, nodo destino, repositorio de tokens. Salidas: diccionario con el token JWT codificado, `jti` y timestamp de expiración.

#### 5. Repositorios de Persistencia (`src/app/repositories.py`)
* **Ubicación exacta:** `src/app/repositories.py`
* **Propósito funcional:** Abstracción de acceso a datos mediante patrón Repositorio y Protocolos tipados (`NodeRepository`, `RecordRepository`, `TokenRepository`, `AuditRepository`), con doble implementación en memoria y Amazon DynamoDB.
* **Funcionamiento interno:**
  * Conexión DynamoDB: `_dynamo_table()` inicializa tablas usando `boto3.resource("dynamodb")`.
  * `DynamoNodeRepository`: Métodos `create_node`, `get_node`, `list_nodes`, `update_node`, `find_by_api_key_hash`.
  * `DynamoRecordRepository`: Operaciones sobre `RecordsTable` y `ReplicasTable`. En `upsert()` implementa `ConditionExpression` para garantizar concurrencia optimista evitando que escrituras desfasadas sobreescriban datos nuevos.
  * `DynamoTokenRepository`: Inserción de tokens con TTL y actualización atómica `update_item` para revocación (`revoked = true`).
  * `DynamoAuditRepository`: Inserción de bitácora mediante `put_item` (inmutable, sin soporte de actualización ni borrado).
* **Entradas y Salidas:** Entradas: diccionarios tipados de dominio. Salidas: registros recuperados, entidades mapeadas o excepciones de integridad (`DuplicateNitError`, `ClientError`).

#### 6. Generador de Reportes PDF (`src/app/reports.py`)
* **Ubicación exacta:** `src/app/reports.py`
* **Propósito funcional:** Compilación dinámica en memoria de documentos ejecutivos y forenses en PDF para la administración de la red.
* **Funcionamiento interno:** Utiliza la librería `reportlab` (canvas, tablas, Flowables, estilos) para compilar en un buffer `io.BytesIO()` el reporte solicitado según 4 modalidades: General, Auditoría Forense, Resiliencia y Fallos, y Directorio de Nodos.
* **Entradas y Salidas:** Entradas: listas de nodos, listas de auditoría y tipo de reporte. Salidas: flujo binario `bytes` con el contenido del archivo PDF.

#### 7. Routers de la API (`src/app/routers/`)
* **`nodes.py` (`POST /api/v1/nodes/register`, `GET /api/v1/nodes/active`):** Registro abierto de solicitudes institucionales y directorio público de nodos autorizados (Service Registry).
* **`admin.py` (`GET /api/v1/admin/nodes`, `POST /api/v1/admin/nodes/{id}/approve`, `PATCH /api/v1/admin/nodes/{id}/status`, `GET /api/v1/admin/reports/network-summary`):** Gestión de ciclo de vida de nodos (aprobación, degradación de salud) y descarga de reportes PDF bajo protección de `X-Admin-Key`.
* **`sync.py` (`POST /api/v1/node/sync-records`):** Carga masiva o actualización de historiales académicos. Escribe simultáneamente en `RecordsTable` (primario) y `ReplicasTable` (réplica) validando la identidad del nodo emisor desde la API Key inyectada.
* **`students.py` (`POST /api/v1/students/token`, `GET /api/v1/students/tokens`, `DELETE /api/v1/students/token/{jti}`):** Autenticación de estudiantes con PBKDF2, emisión de tokens de consentimiento con audiencia específica y revocación instantánea.
* **`federated.py` (`GET /api/v1/federated/academic-history/{student_id}`):** Núcleo del middleware distribuido. Valida nodo consultante, valida JWT (`aud`, firma, vigencia, revocación), ejecuta conmutación a réplica ante caídas simuladas o reales, verifica firma SHA-256 de los datos y genera registro inmutable en auditoría.
* **`audit.py` (`GET /api/v1/audit/logs`):** Consulta filtrada de la bitácora inmutable con cabeceras `Cache-Control: no-store` y soporte de filtrado temporal por parámetro `since`.

---

### 14.2 Frontend Web (`src/app/static/`)

La interfaz de usuario está construida en HTML5 semántico, CSS moderno con variables y capas `@layer`, y JavaScript vanilla modular (ES Modules), sin dependencias externas ni compiladores (Webpack/Vite):

* **`styles.css`:** Sistema de diseño completo en modo dual (claro/oscuro automático con `light-dark()`), tipografía fluida con `clamp()`, grid responsivo y componentes accesibles (foco visible, contraste AA).
* **`common.js`:** Utilidades compartidas (`$`, `api`, `announce`, `setBusy`, `errorText`). Implementa wrapper seguro sobre `fetch` y soporte de accesibilidad para lectores de pantalla (`aria-live`).
* **`inicio.html` (`/`):** Portal de bienvenida y navegación centralizada a los módulos de la red.
* **`registro-nodo.html` y `registro.js` (`/registro-nodo`):** Formulario de registro para universidades con validación en tiempo real de NIT, dominio y correo institucional.
* **`admin.html` y `admin.js` (`/admin`):** Consola para administradores: listado de instituciones, aprobación con emisión visible única de API Key y filtros de estado.
* **`panel-nodo.html` y `panel-nodo.js` (`/panel-nodo`):** Panel para directores de registro. Incluye el generador dinámico de historiales aleatorios (`generateExample()`) para pruebas en vivo y sincronización hacia la nube.
* **`portal-estudiante.html` y `portal-estudiante.js` (`/portal-estudiante`):** Interfaz para que el alumno ingrese con su cédula y contraseña, consulte a qué universidades autorizar, genere su JWT y revoque consentimientos previos.
* **`consulta.html` y `consulta.js` (`/consulta`):** Interfaz de consulta interinstitucional. Permite ingresar el token de consentimiento, forzar simulación de fallo (`X-Simulate-Down`) y visualizar el historial académico junto a la procedencia (`Primary` vs `Replica`).
* **`auditoria.html` y `auditoria.js` (`/auditoria`):** Panel forense en tiempo real para visualizar eventos de acceso, denegaciones, IPs de origen y estados de seguridad con filtro temporal (`since`).
* **`reportes.html` y `reportes.js` (`/reportes`):** Centro de exportación ejecutiva para seleccionar el tipo de informe y descargar el documento PDF compilado en memoria.

---

## 15. Funcionamiento Profundo de Cada Componente en AWS

### 15.1 Desglose por Servicio AWS

```mermaid
flowchart TD
    Client([Navegador / Cliente HTTP]) -->|HTTPS / TLS 1.3| APIGW[Amazon API Gateway\nHTTP API v2]
    
    subgraph Compute["Plano de Cómputo Serverless"]
        APIGW -->|$default route / proxy| Lambda[AWS Lambda\nRuntime Python 3.12]
        Lambda --> Mangum[Adaptador ASGI Mangum]
        Mangum --> FastAPI[FastAPI App Core]
    end

    subgraph Storage["Plano de Datos NoSQL Distribuido"]
        FastAPI -->|Boto3 Table API| T1[(NodesTable\nPK: node_id)]
        FastAPI -->|Boto3 Table API| T2[(RecordsTable\nPK: record_key)]
        FastAPI -->|Boto3 Table API| T3[(ReplicasTable\nPK: record_key)]
        FastAPI -->|Boto3 Table API + TTL| T4[(TokensTable\nPK: jti)]
        FastAPI -->|Boto3 Table API PutOnly| T5[(AuditLogsTable\nPK: log_id)]
    end

    subgraph Observability["Monitoreo y Auditoría"]
        Lambda -.->|Stdout / Stderr| CWL[Amazon CloudWatch Logs\nStreams concurrentes]
    end
```

#### 1. Amazon API Gateway (HTTP API v2)
* **Función:** Actúa como puerta de entrada segura y punto de terminación TLS. Recibe el tráfico en la URL pública, gestiona el protocolo HTTP/2 y redirige todas las rutas hacia la función Lambda mediante integración proxy `$default`.
* **Configuración:** Modo Payload Format Version 2.0, enrutamiento catch-all `/{proxy+}`.

#### 2. AWS Lambda
* **Función:** Ejecutor de cómputo elástico sin servidor. Cada petición que llega a API Gateway despierta o reutiliza un micro-contenedor de Lambda ejecutando el runtime optimizado `python3.12`.
* **Configuración:** Memoria asignada 512 MB, arquitectura x86_64, timeout de 15 segundos.
* **Mapeo en código:** `src/app/main.py` define `handler = Mangum(app, lifespan="off")`, el cual traduce los eventos del API Gateway v2 al protocolo ASGI estándar que FastAPI procesa.

#### 3. Amazon DynamoDB (Plano de Persistencia Distribuida)
Todas las tablas operan bajo la modalidad **On-Demand (Pay-per-request)** y cifrado en reposo con claves gestionadas por AWS KMS:
1. **`NodesTable`:**
   * **Clave de Partición (PK):** `node_id` (Cadena `IES-XXXXXXXX`).
   * **Contenido:** Razón social, NIT, dominio institucional, correo, estado (`PENDIENTE_APROBACION`, `ACTIVO`, `DEGRADADO`), hash SHA-256 de la API Key (`api_key_hash`).
   * **Mapeo:** Invocado en `src/app/repositories.py` (`DynamoNodeRepository`).
2. **`RecordsTable`:**
   * **Clave de Partición (PK):** `record_key` (Cadena compuesta `<node_id>#<student_id>`).
   * **Contenido:** Cédula, nombre completo, programa, materias cursadas con créditos y notas, hash de contraseña y `digital_signature_hash`.
   * **Mapeo:** Invocado en `DynamoRecordRepository` en `repositories.py`.
3. **`ReplicasTable`:**
   * **Clave de Partición (PK):** `record_key`.
   * **Contenido:** Réplica exacta de `RecordsTable` sincronizada en cada operación de carga.
   * **Mapeo:** Gestionada vía `get_replica_repository()` en `repositories.py`.
4. **`TokensTable`:**
   * **Clave de Partición (PK):** `jti` (UUID hexadecimal).
   * **Mecanismo Especial TTL:** Posee habilitado el mecanismo Time-To-Live sobre el atributo `ttl`. DynamoDB elimina de forma autónoma los tokens cuyo timestamp Unix haya caducado.
   * **Mapeo:** Invocado en `DynamoTokenRepository` en `repositories.py` y `tokens.py`.
5. **`AuditLogsTable`:**
   * **Clave de Partición (PK):** `log_id` (Cadena `AUDIT-XXXXXXXXXXXX`).
   * **Característica:** Inmutabilidad estricta. El rol IAM de Lambda solo tiene concedido `dynamodb:PutItem` y `dynamodb:Scan` sobre esta tabla; no existen permisos para `DeleteItem` ni `UpdateItem`.
   * **Mapeo:** Invocado en `DynamoAuditRepository` en `repositories.py`.

#### 4. Amazon CloudWatch Logs
* **Función:** Almacena la salida estándar (`stdout`/`stderr`), logs de excepciones y trazas de ejecución de cada contenedor Lambda.
* **Evidencia Distribuida:** Permite auditar en tiempo real los diferentes `RequestId` ejecutados concurrentemente por distintos hilos de ejecución en la nube.

---

### 15.2 Flujo de Ejecución Milisegundo a Milisegundo

Cuando un funcionario de admisiones pulsa "Consultar Historial" en el cliente web:

1. **ms 0 – ms 15 (Red y TLS):** La petición HTTP sale del navegador hacia `https://ypybm0azfg.execute-api.us-east-2.amazonaws.com`. API Gateway negocia el handshake TLS 1.3 y autentica el certificado wildcard de AWS.
2. **ms 15 – ms 20 (API Gateway Routing):** API Gateway valida la ruta `/api/v1/federated/academic-history/{id}`, empaqueta los encabezados (`X-Node-API-Key`, `X-Student-Consent-Token`), query params y cuerpo en un evento JSON v2 y efectúa la invocación sincrónica a Lambda.
3. **ms 20 – ms 30 (Lambda Initialization / Dispatch):**
   * *Warm Start:* Lambda recibe el evento en un micro-contenedor caliente y se lo entrega al handler de Mangum.
   * Mangum traduce el evento a un scope HTTP de ASGI y lo entrega a FastAPI.
4. **ms 30 – ms 45 (Inyección y Middleware de Seguridad):**
   * FastAPI ejecuta la dependencia `require_node`: calcula SHA-256 de la cabecera `X-Node-API-Key` y llama a `DynamoNodeRepository.find_by_api_key_hash`. DynamoDB retorna en ~6 ms el registro del nodo validando su estado `ACTIVO`.
   * El controlador ejecuta `verify_token`: decodifica el JWT mediante clave secreta simétrica, comprueba que `aud` coincida con el nodo consultante y consulta `TokensTable` por clave `jti` para certificar que `revoked` no sea `True`.
5. **ms 45 – ms 55 (Enrutamiento Federado y Failover):**
   * El sistema intenta leer el registro primario en `RecordsTable` mediante la clave `record_key(origin_node, student_id)`.
   * Si el nodo origen está marcado como caído o falla la lectura, conmuta instantáneamente a `ReplicasTable` extrayendo el historial de contingencia y seteando la cabecera `X-Data-Source: Replica`.
6. **ms 55 – ms 65 (Verificación Criptográfica y Auditoría Inmutable):**
   * Se reconstruye el payload canónico de materias y datos y se calcula `record_signature(signed)`. Se comprueba contra `digital_signature_hash`.
   * Se genera un ID de auditoría único y se efectúa `PutItem` en `AuditLogsTable` con el resultado (`SUCCESS`), IP de origen y fuente de datos.
7. **ms 65 – ms 75 (Respuesta):** Mangum empaqueta la respuesta JSON y los headers de respuesta, API Gateway los retorna sobre la conexión HTTPS abierta y el navegador del usuario renderiza la tabla de asignaturas y créditos completados.

---

## 16. Documentación Interactiva de la API (Swagger / OpenAPI)

### 16.1 ¿Qué es Swagger / OpenAPI y qué aporta al proyecto?
**OpenAPI** es el estándar internacional para describir formalmente APIs REST sin necesidad de inspeccionar el código fuente. **Swagger UI** es la interfaz gráfica generada a partir de dicho estándar que permite a evaluadores y desarrolladores externos:
* Conocer todos los contratos de datos, parámetros y cabeceras exigidas.
* Probar la API de forma interactiva directamente desde el navegador web, sin requerir herramientas de terceros como Postman o cURL.
* Validar en tiempo real los esquemas Pydantic y las respuestas HTTP documentadas.

### 16.2 Funcionamiento Interno en FastAPI
FastAPI inspecciona los modelos Pydantic (`src/app/models.py`), las dependencias de cabeceras (`src/app/security.py`) y las anotaciones de tipo de cada router. Con esto genera dinámicamente un esquema JSON OpenAPI en la ruta:
* **Especificación OpenAPI (JSON):** `/openapi.json`
* **Swagger UI interactivo:** `/docs`
* **Documentación ReDoc:** `/redoc`

Ambas interfaces se encuentran completamente habilitadas tanto en la ejecución local (`http://127.0.0.1:8001/docs`) como en el despliegue cloud de AWS (`https://ypybm0azfg.execute-api.us-east-2.amazonaws.com/docs`).

### 16.3 Guía Práctica de Uso Paso a Paso

```mermaid
flowchart LR
    A[Ingresar a /docs] --> B[Explorar Endpoints]
    B --> C[Click 'Try it out']
    C --> D[Llenar parámetros y Headers]
    D --> E[Click 'Execute']
    E --> F[Inspeccionar Respuesta HTTP y JSON]
```

1. **Acceso:** Abre en tu navegador `https://ypybm0azfg.execute-api.us-east-2.amazonaws.com/docs`.
2. **Autenticación en Swagger:**
   * La API protege sus rutas mediante cabeceras HTTP personalizadas (`X-Admin-Key`, `X-Node-API-Key`, `X-Student-Consent-Token`).
   * Para probar un endpoint restringido, despliega la caja del endpoint (ej. `GET /api/v1/admin/nodes`), haz clic en **Try it out** y rellena directamente el campo `X-Admin-Key` con la clave administrativa configurada.
3. **Ejecución Interactiva:**
   * Completa el cuerpo de la petición (JSON) si es un método POST/PATCH.
   * Pulsa el botón azul **Execute**.
   * Swagger enviará la petición HTTPS real a AWS Lambda y mostrará la URL ejecutada, el código de estado (`200 OK`, `403 Forbidden`, `409 Conflict`, etc.) y el cuerpo de respuesta con las cabeceras recibidas (incluyendo `x-data-source` y `cache-control`).

---

## 17. Conceptos de Sistemas Distribuidos Aplicados al Proyecto

A continuación se fundamentan los conceptos nodales de la disciplina de **Sistemas Distribuidos**, vinculando la teoría académica directamente con su manifestación tangible en el código fuente y los servicios de AWS:

| Concepto de Sistemas Distribuidos | Manifestación en RFHA-IES | Archivo y Función en Código | Recurso AWS |
|---|---|---|---|
| **Nodos Autónomos** | Cada universidad opera como una entidad descentralizada con API Key propia y almacén de datos segregado. No hay acceso cruzado directo entre universidades. | `src/app/security.py` (`new_api_key`, `require_node`) | `NodesTable` |
| **Middleware Federado** | Actúa como plano de control mediador: enruta peticiones, transforma formatos y valida identidades sin concentrar la propiedad de los datos. | `src/app/routers/federated.py` (`academic_history`) | AWS Lambda + API Gateway |
| **Tolerancia a Fallos y Failover** | Conmutación por error automática: si el nodo primario no responde, el sistema consulta de forma transparente el almacén réplica. | `src/app/routers/federated.py` (L.100-114) | `RecordsTable` → `ReplicasTable` |
| **Consistencia Eventual (AP)** | Sacrifica consistencia estricta por disponibilidad total. Replica registros en segundo plano; la réplica representa la versión más reciente sincronizada. | `src/app/routers/sync.py` (`sync_records`) | DynamoDB ReplicasTable |
| **Concurrencia Optimista** | Detección de colisiones mediante condición de escritura atómica para evitar que peticiones atrasadas sobreescriban datos nuevos. | `src/app/repositories.py` (`ConditionExpression` en `upsert`) | DynamoDB Conditional Writes |
| **Autorización Descentralizada** | Consentimiento de acceso gobernado por el usuario mediante tokens JWT de audiencia estricta (`aud`), impidiendo reutilización en nodos no autorizados. | `src/app/tokens.py` (`issue_token`, `verify_token`) | `TokensTable` (con TTL) |
| **Service Registry (Descubrimiento)** | Registro dinámico para que los nodos descubran qué universidades están operativas antes de solicitar o autorizar transferencias. | `src/app/routers/nodes.py` (`active_nodes`) | `NodesTable` (Filter `status=ACTIVO`) |
| **Bitácora Distribuida Inmutable** | Log de transacciones de solo inserción (Append-Only) para trazabilidad forense no repudiable de cada consulta y bloqueo. | `src/app/routers/audit.py` y `repositories.py` (`DynamoAuditRepository`) | `AuditLogsTable` (IAM PutOnly) |

---

## 18. Guía Práctica de Demostración en Vivo (Consola AWS + App)

Esta guía describe el procedimiento exacto para sustentar el proyecto en vivo frente a evaluadores, combinando la aplicación web con la consola de AWS.

### 18.1 Demostración en AWS CloudWatch Logs (Cómputo Concurrente y Stateless)
1. Inicia sesión en la **Consola de AWS** con el perfil correspondiente y navega a **CloudWatch** en la región `us-east-2`.
2. En el menú izquierdo, selecciona **Logs** → **Log groups** y haz clic en `/aws/lambda/rfha-app`.
3. Abre simultáneamente dos navegadores o una ventana en incógnito y realiza consultas en la web (`/consulta` o `/auditoria`).
4. En CloudWatch, abre los flujos de registro (*Log streams*) más recientes:
   * **Evidencia a señalar:** Muestra cómo existen diferentes `Log Streams` ejecutándose en paralelo.
   * Destaca los identificadores de petición únicos (`START RequestId: ...`) y (`REPORT RequestId: ... Duration: 12.4 ms Billed Duration: 13 ms Memory Size: 512 MB`). Explica al docente que esto certifica que el sistema es **completamente stateless y elástico**.

### 18.2 Demostración en Amazon DynamoDB (Particionamiento e Inmutabilidad)
1. En la consola de AWS, dirígete a **Amazon DynamoDB** → **Tables** (región `us-east-2`).
2. **Particionamiento y Réplicas:**
   * Entra a `RecordsTable` → botón **Explore table items**.
   * Muestra la estructura de la clave `record_key` con formato `<node_id>#<student_id>` (ej. `IES-A1B2C3D4#20262678029`).
   * Demuestra que en `ReplicasTable` existe exactamente el mismo registro replicado con su `digital_signature_hash`.
3. **Mecanismo TTL (TokensTable):**
   * Abre `TokensTable` → selecciona la pestaña **Additional settings**.
   * Muestra que el campo **Time to Live (TTL)** está en estado **ENABLED** sobre el atributo `ttl`. Explica cómo esto garantiza la neguentropía del sistema al purgar automáticamente tokens caducados sin consumir cómputo.
4. **Inmutabilidad (AuditLogsTable):**
   * Abre `AuditLogsTable` y muestra cómo cada consulta realizada en la plataforma genera un nuevo registro `AUDIT-XXXXXXXXXXXX` con `timestamp`, `client_ip`, `outcome` y `data_source`.

### 18.3 Demostración en Amazon API Gateway
1. Dirígete a **API Gateway** → selecciona la API `rfha-app`.
2. Muestra las rutas configuradas (`$default`) y en la pestaña de **Stages** (`$default`) evidencia la URL de invocación segura con certificado SSL/TLS gestionado.
3. Muestra las métricas integradas de CloudWatch: número de invocaciones, latencia de integración (< 50 ms) y cero errores 5XX.

### 18.4 Prueba de Fuego: Failover a Réplica y Revocación en Tiempo Real
1. **Sincronización:** En el panel del nodo (`/panel-nodo`), genera datos aleatorios con "Cargar ejemplo" e ingresa la API Key del nodo. Pulsa **Sincronizar historiales**.
2. **Consentimiento:** En el portal del estudiante (`/portal-estudiante`), inicia sesión con el documento y clave de uno de los estudiantes cargados. Autoriza a una universidad receptora y copia el token generado.
3. **Consulta Normal (Primaria):** Ve a `/consulta`, pega el token de autorización y pulsa **Consultar Historial**. Muestra la etiqueta verde de procedencia: **Fuente de datos: Primary**.
4. **Fallo Simulado (Failover Activo):**
   * En la misma pantalla `/consulta`, marca la casilla de verificación **"Simular falla de conectividad con el nodo de origen"** (`X-Simulate-Down: true`).
   * Pulsa nuevamente **Consultar Historial**.
   * **Resultado en vivo:** El sistema no falla; responde de inmediato mostrando la etiqueta ámbar **Fuente de datos: Replica**.
5. **Auditoría Forense Inmediata:**
   * Ve a `/auditoria`, ingresa la clave de administrador y carga la bitácora.
   * Muestra las dos entradas consecutivas: la primera con fuente `Primary` y la segunda con fuente `Replica`, demostrando la trazabilidad inmutable y el funcionamiento en tiempo real.
