# Arquitectura completa y guía de módulos — RFHA-IES

**Red Federada de Historiales Académicos · Versión con HU-01 a HU-10**

> Este documento detalla cómo funciona **cada parte** de la aplicación, cómo se combinan los servicios de AWS con el desarrollo en Python/FastAPI, qué hace cada módulo de código, diagramas de arquitectura y flujo, cómo conectar múltiples máquinas en simultáneo y el análisis de viabilidad para generación de reportes estadísticos en PDF.

---

## Contenido

1. [Vista de pájaro: qué es el sistema](#1-vista-de-pájaro)
2. [Arquitectura AWS + código](#2-arquitectura-aws--código)
3. [Diagrama de capas y componentes](#3-diagrama-de-capas-y-componentes)
4. [Qué hace cada módulo de código](#4-qué-hace-cada-módulo-de-código)
5. [Flujos principales paso a paso](#5-flujos-principales-paso-a-paso)
6. [Las tablas DynamoDB](#6-las-tablas-dynamodb)
7. [Seguridad en detalle](#7-seguridad-en-detalle)
8. [Pantallas del frontend](#8-pantallas-del-frontend)
9. [Módulo de reportes PDF — análisis de viabilidad](#9-módulo-de-reportes-pdf--análisis-de-viabilidad)
10. [Cómo conectar varias máquinas al mismo tiempo (Demostración de Sistema Distribuido)](#10-cómo-conectar-varias-máquinas-al-mismo-tiempo-demostración-de-sistema-distribuido)

---

## 1. Vista de pájaro

RFHA-IES es un **middleware federado** desplegado en AWS (región `us-east-2` Ohio). Permite que diversas Instituciones de Educación Superior (nodos) compartan historiales académicos de estudiantes de forma descentralizada, tolerante a fallos, inmutable y siempre bajo consentimiento explícito del estudiante.

```
Universidad A (Origen)        Universidad B (Consultante)         Estudiante
   (Emite historial)              (Pide historial)           (Autoriza y revoca)
          │                              │                            │
          │ Sincroniza                   │ Consulta                   │ Genera token JWT
          ▼                              ▼                            ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                    RFHA-IES (Middleware Federado)                      │
 │                  FastAPI en AWS Lambda (Python 3.12)                   │
 │                                                                        │
 │  • Valida identidad con API Keys (SHA-256)                             │
 │  • Valida consentimiento con Token JWT (HS256) + Blacklist             │
 │  • Comprueba integridad con Firma SHA-256 de JSON canónico             │
 │  • Detección y Failover automático a réplica autorizada (HU-08)        │
 │  • Registro inmutable de auditoría en DynamoDB (HU-09)                 │
 └──────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
       ┌──────────────────────────────────────────────────────────┐
       │     Almacenamiento Persistente en Amazon DynamoDB        │
       │     NodesTable · RecordsTable · ReplicasTable            │
       │     TokensTable · AuditLogsTable                         │
       └──────────────────────────────────────────────────────────┘
```

**Roles del sistema:**

| Rol | Responsabilidad | Pantalla |
|---|---|---|
| **Administrador General** | Aprueba nodos universitarios, visualiza auditoría global y métricas. | `/admin`, `/auditoria` |
| **Universidad (Nodo)** | Se registra, sincroniza historiales de sus estudiantes y consulta historiales autorizados. | `/registro-nodo`, `/panel-nodo`, `/consulta` |
| **Estudiante** | Ingresa con su cédula, emite tokens de consulta restringidos a una universidad y revoca permisos. | `/portal-estudiante` |

---

## 2. Arquitectura AWS + código

### 2.1 Componentes en AWS

```
Internet (Clientes / Nodos / Estudiantes)
   │ HTTPS (TLS 1.2+)
   ▼
┌──────────────────────────────────────────────────────────────────┐
│  AWS API Gateway (HTTP API - v2)                                 │
│  • Puerta de entrada pública única.                              │
│  • Throttling anti-abuso: máx 20 req/s, ráfaga 50.               │
│  • Transforma peticiones HTTP a eventos JSON estándar ASGI.      │
└──────────────────┬───────────────────────────────────────────────┘
                   │ Invocación (Payload format 2.0)
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│  AWS Lambda: "rfha-app" (Python 3.12 · 1 024 MB · Timeout 29s)   │
│                                                                  │
│  [Mangum Adapter] ── ASGI ──▶ [FastAPI App]                      │
│                                      │                           │
│     ┌────────────────────────────────┴─────────────────────┐     │
│     │ Routers FastAPI:                                     │     │
│     │ • nodes.py     (HU-01 Registro de universidades)     │     │
│     │ • admin.py     (HU-02 Aprobación y API Keys)         │     │
│     │ • sync.py      (HU-03 Carga y réplicas)              │     │
│     │ • students.py  (HU-04/05 Tokens y revocación)        │     │
│     │ • federated.py (HU-06/07/08 Consulta y failover)     │     │
│     │ • audit.py     (HU-09 Bitácora inmutable)            │     │
│     └────────────────────────────────┬─────────────────────┘     │
│                                      │ Inyección de Repositorios │
│     ┌────────────────────────────────▼─────────────────────┐     │
│     │ Repositorios con boto3 (boto3.resource("dynamodb"))  │     │
│     └──────────────────────────────────────────────────────┘     │
└──────────────────┬───────────────────────────────────────────────┘
                   │ HTTPS firmado con AWS Signature V4
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│  Amazon DynamoDB (On-Demand / Pay-Per-Request · sa-east-1)      │
│  • NodesTable: Nodos, estado y hash de API Key                   │
│  • RecordsTable: Historiales académicos primarios con firmas     │
│  • ReplicasTable: Réplicas automáticas para tolerancia a fallos  │
│  • TokensTable: Tokens emitidos, control de intentos y TTL       │
│  • AuditLogsTable: Bitácora inmutable de accesos y bloqueos      │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│  Amazon CloudWatch & AWS Budgets                                 │
│  • Logs en `/aws/lambda/rfha-app` con 7 días de retención.       │
│  • Alerta de presupuesto (Budget SNS) para tope de costo cero.   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 ¿Cómo se combinan AWS y el desarrollo Python?

1. **Sin servidor (Serverless):** No hay servidores EC2 que gestionar ni parches de SO. El código corre en **AWS Lambda** y duerme cuando no hay peticiones, costando cero cuando no se usa.
2. **Mangum como puente:** AWS Lambda no habla HTTP directamente; recibe eventos JSON de API Gateway. La librería `Mangum` toma ese evento JSON, lo transforma en una llamada ASGI que entiende `FastAPI`, y devuelve la respuesta formateada a API Gateway.
3. **Persistencia desacoplada con Patrón Repository:**
   - En desarrollo local (`REPOSITORY_BACKEND=memory`), el código guarda todo en diccionarios en RAM.
   - En AWS (`REPOSITORY_BACKEND=dynamodb`), `repositories.py` usa `boto3` para hablar con las 5 tablas DynamoDB.
   - Los routers de negocio (`routers/`) nunca tocan `boto3` directamente: reciben la interfaz abstracta `RecordRepository`, `NodeRepository`, etc. por inyección de dependencias (`Depends()`).
4. **Seguridad delegada a IAM:** La Lambda se autentica con DynamoDB sin usar credenciales fijas en el código. CloudFormation crea un Rol IAM con políticas `DynamoDBCrudPolicy` restringidas a las 5 tablas exactas. AWS provee credenciales temporales rotativas automáticas.

---

## 3. Diagrama de capas y componentes

```
┌──────────────────────────────────────────────────────────────────────┐
│                    CAPA 1: CLIENTES Y FRONTEND                       │
│  Navegador Web (HTML5 + CSS Vanilla + JS Fetch API)                  │
│  Archivos: inicio.html, registro-nodo.html, admin.html,             │
│            panel-nodo.html, portal-estudiante.html, consulta.html,   │
│            auditoria.html.                                           │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │ JSON vía HTTPS REST
┌──────────────────────────────────▼───────────────────────────────────┐
│                    CAPA 2: ENRUTAMIENTO Y HTTP                       │
│  FastAPI (src/app/main.py)                                           │
│  Mapeo de rutas, encabezados de seguridad CSP, parseo JSON, CORS    │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────┐
│                    CAPA 3: MODELOS Y VALIDACIÓN                      │
│  Pydantic (src/app/models.py)                                        │
│  Validación estricta de regex de NIT, cédula, esquemas de cursos,    │
│  notas de 0.0 a 5.0, estados válidos y serialización JSON.           │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────┐
│              CAPA 4: LÓGICA DE NEGOCIO Y CONTROLADORES               │
│  Routers (src/app/routers/):                                         │
│  • nodes.py     • admin.py      • sync.py                            │
│  • students.py  • federated.py  • audit.py                           │
└──────────────────┬─────────────────────────────────┬─────────────────┘
                   │                                 │
┌──────────────────▼─────────────────┐ ┌─────────────▼─────────────────┐
│     CAPA 5: SEGURIDAD Y TOKENS     │ │   CAPA 6: ACCESO A DATOS      │
│  • security.py:                    │ │  • repositories.py:           │
│    - hash_api_key (SHA-256)        │ │    - NodeRepository           │
│    - hash_password (PBKDF2-SHA256) │ │    - RecordRepository         │
│    - record_signature (SHA-256)    │ │    - TokenRepository          │
│    - verify_password (Timing-safe) │ │    - AuditRepository          │
│  • tokens.py:                      │ │                               │
│    - issue_token / verify_token    │ │  Implementaciones:            │
│    - JWT HS256 + TTL 24h           │ │  - InMemory (Local)           │
│    - Control Blacklist (jti)       │ │  - DynamoDB (AWS)             │
└────────────────────────────────────┘ └──────────────┬────────────────┘
                                                      │
┌─────────────────────────────────────────────────────▼────────────────┐
│                    CAPA 7: ALMACENAMIENTO AWS                        │
│  Amazon DynamoDB (Tablas NoSQL con claves de partición)              │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Qué hace cada módulo de código

### 4.1 `src/app/main.py`
- Instancia la aplicación `FastAPI`.
- Configura las cabeceras de seguridad estrictas (`Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`).
- Registra las páginas estáticas del frontend y los 6 routers de la API.
- Exporta el `handler = Mangum(app, lifespan="off")` para ejecución en AWS Lambda.

### 4.2 `src/app/config.py`
- Carga variables de entorno locales desde `.env` si existe.
- Lee los parámetros inyectados por CloudFormation: nombres de las 5 tablas DynamoDB, `JWT_SECRET`, `ADMIN_KEY`, `SIMULATE_NODE_DOWN` y el backend de datos (`dynamodb` vs `memory`).

### 4.3 `src/app/models.py`
- Define los contratos de datos y reglas de negocio con Pydantic.
- Valida tipos de datos, rangos y expresiones regulares (NIT colombiano, dominios educativos, cédulas de 5 a 15 dígitos, notas válidas de 0.0 a 5.0).
- Modela las estructuras de auditoría, réplicas, sincronización y respuestas de token.

### 4.4 `src/app/security.py`
- **API Keys de universidades:** Generación con `secrets.token_urlsafe(32)` y almacenamiento únicamente de su digest `SHA-256`.
- **Contraseñas de estudiantes:** Hashing mediante `PBKDF2-HMAC-SHA256` con 100 000 iteraciones y sal criptográfica de 16 bytes. Comparación en tiempo constante para evitar ataques de temporización.
- **Firma digital de historiales:** Serialización JSON canónica (claves ordenadas alfabéticamente, sin espacios extras) firmada con `SHA-256`.
- **Dependencias de control de acceso:** `require_admin` para validar la clave maestra y `require_node` para verificar que la universidad esté activa y su API Key coincida.

### 4.5 `src/app/tokens.py`
- Creación de tokens de consentimiento estudiantil en formato `JWT HS256`.
- Inclusión de claims estándar y federados: `sub` (estudiante), `doc` (cédula), `origin` (nodo emisor), `aud` (nodo destino autorizado), `jti` (identificador único), `iat` y `exp` (vigencia de 24 horas).
- Validación de firma, vigencia, correspondencia de audiencia (`aud`) y chequeo en tiempo real contra la lista negra de revocación en `TokensTable`.

### 4.6 `src/app/repositories.py`
- Abstracción mediante `typing.Protocol` de las 4 interfaces de almacenamiento.
- Manejo de tipos de DynamoDB: conversión de números flotantes a `Decimal` de boto3.
- Operaciones `Scan`, `GetItem`, `PutItem` y `UpdateItem`.
- Garantiza que `AuditRepository` sea de **solo anexado** (`PutItem`), impidiendo ediciones o borrados de auditoría.

### 4.7 Routers de funcionalidades
- **`routers/nodes.py` (HU-01):** Registro público de universidades y catálogo público de universidades activas.
- **`routers/admin.py` (HU-02):** Listado de solicitudes de nodos para el administrador y aprobación con emisión de API Key en un solo paso.
- **`routers/sync.py` (HU-03, HU-08):** Ingesta masiva de historiales por la universidad titular, cálculo de estados de asignaturas, cálculo de firma digital y almacenamiento simultáneo en el nodo primario y en el nodo réplica.
- **`routers/students.py` (HU-04, HU-05):** Autenticación de estudiantes con limitador de 5 intentos fallidos (bloqueo de 15 minutos), emisión de tokens hacia un destino específico, visualización de autorizaciones vigentes y revocación inmediata por `jti`.
- **`routers/federated.py` (HU-06, HU-07, HU-08, HU-09):** Orquestador central de la consulta federada. Ejecuta los 7 controles de validación, conmuta automáticamente a la réplica autorizada si el nodo primario está caído, recalcula y valida la firma digital, e inyecta la bitácora inmutable en `AuditLogsTable`.
- **`routers/audit.py` (HU-09):** Consulta de bitácora con control de acceso granular (administrador ve toda la red, universidad ve solo eventos donde participó).

---

## 5. Flujos principales paso a paso

### 5.1 Flujo Integral: Desde el registro hasta la consulta autorizada

```
[Univ. A: EAN]             [Admin Central]          [Estudiante]          [Univ. B: Nacional]
      │                           │                       │                        │
      ├─ 1. Solicita Registro ───▶│                       │                        │
      │   (NIT, dominio, correo)  │                       │                        │
      │                           ├─ 2. Aprueba Nodo      │                        │
      │◀── Recibe API Key ────────┤     (Emite API Key)   │                        │
      │    (rfha_xxxx)            │                       │                        │
      │                           │                       │                        │
      ├─ 3. Sincroniza Historiales                        │                        │
      │    (Almacena en Primario y Réplica)               │                        │
      │                                                   │                        │
      │                                                   ├─ 4. Ingresa al Portal  │
      │                                                   │     (Cédula + Clave)   │
      │                                                   │                        │
      │                                                   ├─ 5. Emite Autorización │
      │                                                   │     (Destino: Univ. B) │
      │                                                   │     (Obtiene Token)    │
      │                                                   │                        │
      │                                                   │── Entrega Token ──────▶│
      │                                                   │                        │
      │                                                   │                        ├─ 6. Consulta Historial
      │                                                   │                        │    (API Key B + Token)
      │                                                   │                        │
      │◀────────────────── Valida y entrega historial ─────────────────────────────┤
      │                   (Verifica firmas e inyecta auditoría)                    │
```

---

## 6. Las tablas DynamoDB

| Tabla | Clave Primaria (PK) | Atributos Principales | Propósito |
|---|---|---|---|
| **`NodesTable`** | `node_id` (S) | `nit`, `name`, `domain`, `status`, `api_key_hash`, `approved_at` | Directorio de instituciones federadas y credenciales de acceso. |
| **`RecordsTable`** | `record_key` (S) = `<node_id>#<student_id>` | `document_number`, `full_name`, `program`, `courses`, `password_hash`, `digital_signature_hash` | Historiales académicos originales de cada nodo institucional. |
| **`ReplicasTable`** | `record_key` (S) = `<node_id>#<student_id>` | Idénticos a RecordsTable | Copia espejo desacoplada utilizada en caso de indisponibilidad del nodo titular. |
| **`TokensTable`** | `jti` (S) | `document_number`, `student_id`, `aud`, `origin`, `exp`, `revoked`, `ttl` | Registro de tokens de consentimiento, revocaciones y control de intentos fallidos. |
| **`AuditLogsTable`** | `log_id` (S) | `timestamp`, `consulting_node_id`, `target_student_id`, `origin_node_id`, `outcome`, `reason`, `data_source`, `client_ip` | Trazabilidad inmutable de todas las operaciones de consulta federada. |

---

## 7. Seguridad en detalle

1. **Defensa en Profundidad:**
   - Cifrado en tránsito con TLS 1.2+ en todas las capas.
   - Cifrado en reposo automático de AWS DynamoDB (KMS administrado por AWS sin sobrecosto).
2. **Autenticación sin credenciales fijas:**
   - Las contraseñas de estudiantes nunca se guardan en texto plano (PBKDF2 con 100k iteraciones).
   - Las API Keys institucionales solo existen en memoria del cliente; la base de datos solo almacena su hash SHA-256.
3. **No repudio e Integridad de Historiales:**
   - Cada historial posee un campo `digital_signature_hash`. Si algún registro es adulterado en la base de datos, la consulta federada detecta la incongruencia y corta la entrega con código HTTP 500.
4. **Protección contra ataques de fuerza bruta:**
   - Bloqueo por cédula de 15 minutos al quinto intento fallido consecutivo.
   - Duración de verificación timing-safe: verificar una cédula que no existe toma exactamente el mismo tiempo que una existente.

---

## 8. Pantallas del frontend

El sistema cuenta con un frontend responsivo y ligero, sin compiladores pesados ni dependencias externas:

- **`/` (Inicio):** Portal de bienvenida que explica el funcionamiento en 4 pasos y da acceso directo a cada módulo.
- **`/registro-nodo`:** Formulario institucional de alta para nuevas universidades.
- **`/admin`:** Consola del administrador para autorizar solicitudes pendientes y generar credenciales de un solo uso.
- **`/panel-nodo`:** Panel para que las universidades carguen y actualicen lotes de estudiantes.
- **`/portal-estudiante`:** Espacio del alumno para expedir tokens con tiempo de caducidad y revocar permisos previos.
- **`/consulta`:** Interfaz de las universidades receptoras para consultar datos de homologación o transferencias mediante el token del estudiante.
- **`/auditoria`:** Centro de monitoreo inmutable para auditar accesos, orígenes de datos y motivos de denegación.

---

## 9. Módulo de reportes PDF — Implementación y tipos de informes

### 9.1 Estado de Implementación
El módulo está **100% implementado y operativo en producción en AWS**. Utiliza la librería `reportlab` compilando el documento completamente en memoria (`io.BytesIO`) en un tiempo de 200 a 400 ms sin tocar disco.

### 9.2 Los 4 tipos de reportes disponibles

| Tipo | Query Param | Contenido del PDF | Uso en sustentación |
|---|---|---|---|
| **📊 Reporte Ejecutivo Completo** | `type=general` | Visión global: total de nodos, volumen porcentual de consultas, indicadores de resiliencia y muestra de auditoría reciente. | Presentación ejecutiva del proyecto. |
| **🛡️ Bitácora Forense de Seguridad** | `type=auditoria` | Desglose de accesos: tasas de éxito (`SUCCESS`), denegaciones por falta de consentimiento (`DENIED`), errores y los últimos 35 registros con IP del cliente. | Sustentar no repudio, trazabilidad y control de acceso. |
| **⚡ Diagnóstico de Tolerancia a Fallos** | `type=resiliencia` | Métricas de disponibilidad: consultas atendidas por nodo primario vs réplica (**HU-08**) y tabla de conmutaciones/failover. | Sustentar **Sistemas Distribuidos** y el teorema CAP. |
| **🏛️ Catálogo de Instituciones** | `type=nodos` | Directorio institucional completo: ID de nodo, institución, NIT, dominio y estado de aprobación. | Demostrar gobierno federado y descentralización. |

### 9.3 Arquitectura del Módulo

```
Admin (Frontend /admin o /reportes)
   │ Selecciona tipo de reporte y envía X-Admin-Key
   ▼
GET /api/v1/admin/reports/network-summary?type={general|auditoria|resiliencia|nodos}
   │
   ▼
AWS Lambda (FastAPI)
   ├── Consulta AuditRepository.list_logs()
   ├── Consulta NodeRepository.list_nodes()
   ├── Procesa métricas (agrupaciones, contadores)
   ├── Genera PDF en memoria (io.BytesIO) usando ReportLab
   └── Retorna Response(content=pdf_bytes, media_type="application/pdf")
```

---

## 10. Cómo conectar varias máquinas al mismo tiempo (Demostración de Sistema Distribuido)

Para sustentar ante los profesores de **Sistemas Distribuidos** y **Teoría General de Sistemas**, se debe evidenciar que el sistema opera de manera concurrente entre múltiples nodos independientes.

### 10.1 Preparación del Escenario de Prueba Distribuido

Se disponen **3 o más dispositivos físicos** (pueden ser portátiles de estudiantes, PCs de laboratorio o incluso teléfonos móviles conectados por Wi-Fi o datos móviles):

| Dispositivo | Rol Asignado | Acción |
|---|---|---|
| **Máquina 1 (Profesor / Auditor)** | Administrador General | Conectado a `/admin` y `/auditoria` observando en tiempo real. |
| **Máquina 2 (Universidad EAN)** | Nodo Emisor / Origen | Conectado a `/panel-nodo` con su propia API Key institucional. |
| **Máquina 3 (Univ. Nacional)** | Nodo Receptor / Consultante | Conectado a `/consulta` con su respectiva API Key. |
| **Máquina 4 (Dispositivo Móvil)** | Estudiante | Conectado a `/portal-estudiante` con su cédula. |

Todas las máquinas apuntan a la URL pública de AWS Lambda / API Gateway:
`https://<api-id>.execute-api.sa-east-1.amazonaws.com/`

### 10.2 Demostración Paso a Paso de Concurrencia y Distribución

1. **Prueba de Autonomía de Nodos (Concurrencia real):**
   - Máquina 2 y Máquina 3 ejecutan operaciones simultáneas: una sincroniza un lote de registros mientras la otra intenta consultar.
   - **Cómo evidenciarlo:** En la consola de AWS CloudWatch (`/aws/lambda/rfha-app`), el profesor verá registros con diferentes `RequestId` ejecutándose en el mismo segundo exacto, confirmando que AWS instanció **múltiples entornos de ejecución en paralelo**.
2. **Prueba de Trazabilidad por IP de Clientes:**
   - La Máquina 1 recarga `/auditoria`.
   - En la columna **IP Origen**, se apreciarán direcciones IP públicas completamente distintas para cada solicitud, demostrando que las peticiones vinieron de terminales físicas separadas a través de la red.
3. **Prueba de Tolerancia a Fallos en Vivo (HU-08 Failover):**
   - Se activa la simulación de caída para la Universidad A.
   - La Máquina 3 hace una consulta: la petición **no falla**. Retorna el historial exitosamente y en la cabecera / pantalla se muestra `data_source: Replica`.
   - Se demuestra la propiedad de **disponibilidad** del teorema CAP.
4. **Prueba de Consistencia y Revocación Distribuida (HU-05 y HU-07):**
   - La Máquina 3 realiza una consulta exitosa con el token del estudiante.
   - Desde la Máquina 4 (teléfono), el estudiante presiona **Revocar**.
   - En ese mismo instante, la Máquina 3 vuelve a presionar **Consultar**: la solicitud es **bloqueada de inmediato (HTTP 403)**.
   - Esto demuestra la consistencia del estado federado entre todos los nodos sin retardo de propagación.

---
*Documentación oficial de arquitectura del proyecto RFHA-IES · 2026*
