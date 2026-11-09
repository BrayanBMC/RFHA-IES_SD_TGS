# RFHA-IES — Credenciales, Casos de Prueba y Guía de la Consola de AWS

Este documento contiene **todas las credenciales maestras, usuarios ficticios de prueba, claves de acceso y la guía paso a paso para navegar la consola de AWS**, diseñada para sustentar y explicar el funcionamiento del sistema a los docentes y evaluadores de las asignaturas **Sistemas Distribuidos** y **Teoría General de Sistemas**.

> [!NOTE]
> Todos los datos contenidos en este documento (cédulas, notas, nombres e instituciones) son **ficticios y con fines estrictamente académicos**.

---

## 1. Direcciones de Acceso Rápido

### En la Nube (AWS — Plan B)
| Módulo | Dirección Web | Propósito |
|---|---|---|
| **Menú de Inicio** | https://ypybm0azfg.execute-api.us-east-2.amazonaws.com | Portal central de navegación |
| **Registro de Nodos** | https://ypybm0azfg.execute-api.us-east-2.amazonaws.com/registro-nodo | Inscripción de nuevas universidades (HU-01) |
| **Administración General** | https://ypybm0azfg.execute-api.us-east-2.amazonaws.com/admin | Aprobación de universidades y emisión de API Keys (HU-02) |
| **Panel del Nodo IES** | https://ypybm0azfg.execute-api.us-east-2.amazonaws.com/panel-nodo | Carga y sincronización de historiales (HU-03) |
| **Portal del Estudiante** | https://ypybm0azfg.execute-api.us-east-2.amazonaws.com/portal-estudiante | Generación y revocación de tokens de consentimiento (HU-04, HU-05) |
| **Consulta Federada** | https://ypybm0azfg.execute-api.us-east-2.amazonaws.com/consulta | Consulta interinstitucional de expedientes (HU-06, HU-07) |
| **Documentación OpenAPI** | https://ypybm0azfg.execute-api.us-east-2.amazonaws.com/docs | Swagger UI interactivo |

*(En entorno local, reemplaza la base por `http://127.0.0.1:8001` tras ejecutar `.\run-app.cmd`).*

---

## 2. Credencial Maestra de Administración

Para acceder al módulo de **Administración General** (`/admin`):

| Parámetro | Valor |
|---|---|
| **Clave de Administrador (`ADMIN_KEY`)** | `9HoNCx-f21YQc-19oUNnSeI5I3Kk-Pe-` |
| **Dónde se usa** | En la pantalla `/admin` |
| **Cómo ingresar** | Pega la clave en el campo *Clave de administrador* y haz clic en **Cargar solicitudes** |

**Qué puedes hacer en `/admin`:**
* Ver solicitudes pendientes de aprobación.
* Aprobar nuevas instituciones universitarias.
* El sistema emite la API Key institucional una sola vez y almacena únicamente su huella SHA-256.

---

## 3. Universidades Activas y sus API Keys

Las siguientes 4 universidades ya se encuentran registradas y activas en la base de datos de DynamoDB en AWS:

| Institución | Código de Nodo (`node_id`) | NIT | Dominio | API Key del Nodo (`X-Node-API-Key`) |
|---|---|---|---|---|
| **Universidad Distrital Francisco José de Caldas** | `IES-1111AAAA` | `899999230-7` | `udistrital.edu.co` | `rfha_udistrital_prod_key_2026_sec` |
| **Universidad Nacional de Colombia** | `IES-2222BBBB` | `899999063-3` | `unal.edu.co` | `rfha_unal_prod_key_2026_secure99` |
| **Pontificia Universidad Javeriana** | `IES-3333CCCC` | `860007386` | `javeriana.edu.co` | `rfha_javeriana_prod_key_2026_sec` |
| **Universidad de los Andes** | `IES-4444DDDD` | `860007373-4` | `uniandes.edu.co` | `rfha_uniandes_prod_key_2026_sec9` |

### ¿Dónde se usan estas API Keys?
1. **En `/panel-nodo`:** La universidad pega su API Key para autenticarse y cargar o actualizar el lote de historiales de sus estudiantes.
2. **En `/consulta`:** El funcionario de registro de una universidad pega su API Key para autenticar a la institución consultante antes de solicitar el historial de un estudiante.

---

## 4. Catálogo de Estudiantes y Casos de Prueba

Los siguientes 6 estudiantes están activos en la base de datos de AWS y cubren diferentes situaciones académicas:

| # | Estudiante | Cédula / Documento | Contraseña | Código Estudiantil | Universidad Origen | Programa | Estado | Promedio | Propósito del Caso de Prueba |
|---|---|---|---|---|---|---|---|---|---|
| **1** | **Brayan Acosta Parrado** | `1012345678` | `Clave-2026-A` | `20262678029` | U. Distrital (`IES-1111AAAA`) | Ing. en Telemática | **ACTIVO** | 4.52 | Caso feliz principal: materias avanzadas y una materia en curso. |
| **2** | **Juan Sebastián Pardo Gil** | `1019876543` | `Clave-Juan-2026` | `20221050914` | U. Distrital (`IES-1111AAAA`) | Ing. Industrial | **RETIRADO** | 3.21 | Estudiante retirado con materias reprobadas (Física 2.8) y repetidas (3.4). Transferencia externa. |
| **3** | **Laura Camila Ríos Herrera** | `1098765432` | `Clave-2026-B` | `20251234501` | U. Nacional (`IES-2222BBBB`) | Ing. de Sistemas | **ACTIVO** | 4.18 | Homologación con nota mínima exigente (Cálculo Integral 3.4). |
| **4** | **María Fernanda Ospina Duarte** | `1024681357` | `Clave-Maria-2026` | `20252345678` | U. Nacional (`IES-2222BBBB`) | Estadística | **ACTIVO** | 3.88 | Estudiante de primeros semestres: homologación de ciclo básico. |
| **5** | **Andrés Felipe Moreno Castro** | `1035792468` | `Clave-Andres-2026` | `20241122002` | U. Javeriana (`IES-3333CCCC`) | Ing. Electrónica | **GRADUADO** | 4.31 | Validación y convalidación de título profesional sin certificados en papel. |
| **6** | **Valentina Torres Quintero** | `1046801357` | `Clave-Vale-2026` | `20231098763` | U. de los Andes (`IES-4444DDDD`) | Economía | **ACTIVO** | 4.68 | Excelencia académica: solicitud de becas interinstitucionales o posgrados. |

---

## 5. Guía de Ejecución de Pruebas Escena por Escena

### Escena 1: Flujo Completo de Consentimiento y Consulta (Camino Feliz)
1. **Entrar al Portal del Estudiante** (`/portal-estudiante`):
   * Documento: `1012345678`
   * Contraseña: `Clave-2026-A`
   * Pulsa **Ingresar**.
2. **Generar la Autorización:**
   * Selecciona como universidad destino: `Universidad Nacional de Colombia`.
   * Pulsa **Generar autorización**.
   * Se genera un JWT de 24 horas. Pulsa **Copiar token**.
3. **Realizar la Consulta Federada** (`/consulta`):
   * Como funcionario de la Universidad Nacional, ingresa:
     * API Key del funcionario: `rfha_unal_prod_key_2026_secure99` (de la U. Nacional).
     * Código del estudiante: `20262678029` (código de Brayan).
     * Token de consentimiento: Pega el token copiado en el paso anterior.
   * Pulsa **Consultar historial**.
4. **Resultado:**
   * Se superan todos los controles de seguridad.
   * Aparece el expediente con asignaturas, créditos acumulados y la cabecera `X-Data-Source: Primary`.
   * **Explicación al docente:** Los datos nunca salieron de la U. Distrital; el middleware resolvió la procedencia del dato mediante el claim `origin` del token y verificó la firma digital de integridad.

---

### Escena 2: Revocación Instantánea del Consentimiento (Lista Negra)
1. Vuelve a `/portal-estudiante` con Brayan (`1012345678` / `Clave-2026-A`).
2. En la tabla **Tus autorizaciones**, ubica el token que acabas de generar y pulsa el botón **Revocar**.
3. El estado cambia inmediatamente a `REVOCADO`.
4. Vuelve a `/consulta` y pulsa **Consultar historial** con el mismo token:
5. **Resultado:**
   * El sistema responde **HTTP 403 (Acceso denegado)**: *«El token fue revocado por el estudiante en la lista negra»*.
   * **Explicación al docente:** Aunque el JWT sigue vigente en tiempo y su firma criptográfica es auténtica, el middleware consulta la lista negra en `TokensTable` (`revoked: true`) y bloquea la consulta de forma inmediata.

---

### Escena 3: Rechazo por Universidad Destino No Autorizada (Audiencia JWT)
1. Con Laura Ríos (`1098765432` / `Clave-2026-B`), genera un token en `/portal-estudiante` dirigido **únicamente a la Universidad de los Andes**.
2. Copia el token.
3. En `/consulta`, intenta consultar el historial usando la API Key de la **Pontificia Universidad Javeriana** (`rfha_javeriana_prod_key_2026_sec`).
4. **Resultado:**
   * Respuesta **HTTP 403**: *«El token no fue emitido para esta universidad»*.
   * **Explicación al docente:** El claim `aud` (audience) del JWT garantiza que el permiso otorgado por el estudiante sea intransferible entre universidades.

---

### Escena 4: Detección de Falsificación de Datos (Firma Digital Alterada)
1. Si un administrador malintencionado modificara una nota directamente en la base de datos de DynamoDB (por ejemplo, subir una nota de 2.0 a 5.0):
2. El middleware recalcula en tiempo real el SHA-256 canónico del historial (`record_signature`) y lo compara con `digital_signature_hash`.
3. Al no coincidir, el servidor rechaza la respuesta con **HTTP 500** e impide que datos adulterados se entreguen a otra institución.

---

### Escena 5: Protección Contra Ataques de Fuerza Bruta
1. En `/portal-estudiante`, escribe el documento `1012345678` y una contraseña equivocada `clave_erronea`.
2. Pulsa **Ingresar** 5 veces seguidas.
3. Al quinto fallo, la respuesta cambia a **HTTP 429**: *«Demasiados intentos fallidos. La cédula queda bloqueada 15 minutos»*.
4. Ni siquiera ingresando la contraseña correcta se permite el acceso hasta que transcurra el tiempo de enfriamiento registrado en DynamoDB (`LOCK#<cedula>`).

---

## 6. Guía Paso a Paso: Cómo Navegar la Consola de AWS

Esta sección está diseñada para guiar al profesor a través de la consola web de AWS (https://console.aws.amazon.com/) y demostrar la arquitectura serverless, la seguridad en reposo y el cumplimiento del costo cero.

> [!IMPORTANT]
> Asegúrate de que en la esquina superior derecha de la consola de AWS esté seleccionada la región **US East (Ohio) us-east-2**.

---

### 6.1 Amazon DynamoDB (Persistencia NoSQL y Seguridad en Reposo)

1. En la barra superior de búsqueda, escribe `DynamoDB` y haz clic en el servicio.
2. En el menú lateral izquierdo, haz clic en **Tables** (Tablas).
3. Verás las 3 tablas del stack `rfha-app`:
   * `rfha-app-NodesTable-...`
   * `rfha-app-RecordsTable-...`
   * `rfha-app-TokensTable-...`

#### Qué mostrarle al profesor en cada tabla:

* **En `NodesTable` (Catálogo de Nodos):**
  1. Haz clic sobre la tabla y selecciona el botón superior derecho **Explore table items** (Explorar elementos de la tabla).
  2. Abre el registro de `IES-1111AAAA` (Universidad Distrital).
  3. **Punto clave:** Muestra el atributo `api_key_hash`. Explica que la API Key **nunca se guarda en texto claro**, sino como un hash SHA-256. Si un atacante extrajera una copia de la base de datos, no podría utilizar ninguna clave de API.

* **En `RecordsTable` (Historiales Académicos):**
  1. Haz clic en **Explore table items**.
  2. Abre el registro de Brayan (`IES-1111AAAA#20262678029`).
  3. **Punto clave 1:** Muestra el atributo `password_hash`. Explica que la contraseña del estudiante está protegida con **PBKDF2-HMAC-SHA256 con 100,000 iteraciones y sal aleatoria**.
  4. **Punto clave 2:** Muestra el atributo `digital_signature_hash`. Explica que es la huella digital criptográfica del expediente que garantiza que las notas no fueron alteradas en la base de datos.
  5. Muestra la lista de asignaturas (`courses`) guardada como un documento JSON nativo (estructura flexible y heterogénea).

* **En `TokensTable` (Lista Negra y Ciclo de Vida del Consentimiento):**
  1. Haz clic en **Explore table items**.
  2. Verás los tokens generados por los estudiantes identificados por su `jti`.
  3. **Punto clave 1:** Muestra el atributo `revoked` (booleano). Cuando el estudiante pulsa "Revocar", este campo pasa a `true`.
  4. **Punto clave 2 (Mecanismo TTL):** En la pestaña **Additional settings** (Ajustes adicionales) de la tabla, muestra la sección **Time to Live (TTL)** habilitada sobre el atributo `ttl`. Explica que DynamoDB purga automáticamente los registros expirados sin costo de cómputo ni operaciones de escritura facturables.

---

### 6.2 AWS Lambda (Middleware Serverless)

1. En la barra de búsqueda, escribe `Lambda` y entra al servicio.
2. En el menú izquierdo, haz clic en **Functions** (Funciones).
3. Haz clic en la función **`rfha-app`**.

#### Qué mostrarle al profesor:
1. **Pestaña Code (Código):**
   * Muestra la estructura empaquetada: FastAPI, modelos Pydantic, adaptadores de repositorios y el adaptador Mangum (`main.py` -> `handler = Mangum(app)`).
   * Explica que Mangum traduce los eventos de API Gateway en peticiones ASGI estándar sin necesidad de servidores dedicados como Nginx o Gunicorn.
2. **Pestaña Configuration -> Environment variables (Variables de Entorno):**
   * Muestra las variables configuradas:
     * `REPOSITORY_BACKEND = dynamodb`
     * `NODES_TABLE`, `RECORDS_TABLE`, `TOKENS_TABLE`
     * `JWT_SECRET` y `ADMIN_KEY`
   * Explica que ningún secreto está quemado en el repositorio de Git; CloudFormation los inyecta al desplegar de forma segura.
3. **Pestaña Configuration -> Permissions (Principio de Menor Privilegio):**
   * Muestra el rol IAM `AppFunctionRole`.
   * Explica que la Lambda no tiene permisos de administrador general, sino únicamente políticas de lectura y escritura restringidas a sus tres tablas de DynamoDB.
4. **Pestaña Monitor (Métricas en Tiempo Real):**
   * Muestra los gráficos de **Invocations** (Invocaciones), **Duration** (Duración en ms) y **Error count** (0 errores).
   * Destaca los tiempos de respuesta inferiores a 300 ms en ejecuciones regulares (demostrando el cumplimiento del requerimiento RF-05).

---

### 6.3 Amazon API Gateway (Puerta de Entrada y Protección Anti-DoS)

1. En la barra de búsqueda, escribe `API Gateway`.
2. Haz clic en la API de la aplicación (`rfha-app` o ID `ypybm0azfg`).

#### Qué mostrarle al profesor:
1. **Tipo de API:** Mostrar que es una **HTTP API** (versión moderna v2 de API Gateway, más rápida y de menor consumo de recursos que las REST APIs tradicionales).
2. **Rutas (Routes):**
   * Muestra la ruta raíz `ANY /` y la ruta comodín `ANY /{proxy+}`.
   * Ambas están enrutadas a la función Lambda `rfha-app`.
3. **Control de Flujo (Throttling / Protección Anti-DoS):**
   * En **Stages** -> `$default` -> **Route overrides**:
   * Muestra el límite configurado: **Rate limit = 20 req/s** y **Burst limit = 50 req/s**.
   * Explica que esta capa frena ataques de denegación de servicio antes de que lleguen a la Lambda o a la base de datos, garantizando la estabilidad del sistema sin incurrir en costos.

---

### 6.4 Amazon CloudWatch Logs (Trazabilidad y Auditoría)

1. En la barra de búsqueda, escribe `CloudWatch`.
2. En el menú lateral izquierdo, ve a **Logs** -> **Log groups** (Grupos de registros).
3. Haz clic en `/aws/lambda/rfha-app`.

#### Qué mostrarle al profesor:
1. **Política de Retención:** Muestra que **Retention** está configurada en **7 days** (1 semana). Explica que los registros se borran automáticamente para no ocupar almacenamiento innecesario ni generar costos ocultos.
2. **Log Streams (Flujos de registro):**
   * Abre el flujo más reciente.
   * Muestra las líneas `START`, las líneas de log del middleware con cada paso de validación y la línea `REPORT`:
     ```text
     REPORT RequestId: ... Duration: 23.45 ms Billed Duration: 24 ms Memory Size: 1024 MB Max Memory Used: 98 MB
     ```
   * Explica que cada consulta queda auditada con su duración real, memoria utilizada y Request ID único.

---

### 6.5 AWS CloudFormation (Infraestructura como Código — IaC)

1. En la barra de búsqueda, escribe `CloudFormation`.
2. En **Stacks**, selecciona **`rfha-app`**.

#### Qué mostrarle al profesor:
1. **Pestaña Resources (Recursos):**
   * Muestra la lista de los 10 recursos creados: API Gateway, Lambda, Tablas DynamoDB, Roles IAM, permisos y grupos de logs.
   * Explica que no se creó ningún recurso manualmente con clics en la consola; toda la infraestructura está codificada en el archivo declarativo `template.yaml`.
2. **Pestaña Outputs:**
   * Muestra la URL generada (`AppUrl`) y los nombres físicos asignados a cada tabla.
3. **Pestaña Template:**
   * Muestra la plantilla YAML original que orquesta el despliegue automático del sistema.

---

### 6.6 Facturación y Costo Cero (Billing & Cost Management)

1. En la barra de búsqueda, escribe `Billing and Cost Management`.
2. Haz clic en **Bills** (Facturas) en el menú lateral.
3. **Muestra el total facturado:** **$0.00 USD**.
4. Haz clic en **Free Tier** (Capa gratuita) y muestra los consumos porcentuales:
   * AWS Lambda: Una fracción mínima del millón de peticiones gratuitas mensuales.
   * DynamoDB: 25 GB gratuitos de almacenamiento y lecturas bajo demanda cubiertas.
   * API Gateway: Cubierto por el plan de créditos estudiantiles/académicos.

---

## 7. Scripts de Utilidad para la Exposición

En la carpeta `scripts/` se incluyen herramientas para preparar o reiniciar el entorno en cualquier momento:

### Para volver a sembrar los datos de prueba en AWS:
Si se limpiaron las tablas o se requiere restaurar los 4 nodos y los 6 estudiantes iniciales:
```powershell
.\.venv\Scripts\python.exe scripts\seed_sample_data.py --profile rfha --region us-east-2
```

### Para vaciar las tablas antes o después de la exposición:
```powershell
# Solo contar cuántos registros hay:
.\.venv\Scripts\python.exe scripts\clean_aws_data.py --profile rfha --region us-east-2

# Confirmar y vaciar todas las tablas:
.\.venv\Scripts\python.exe scripts\clean_aws_data.py --profile rfha --region us-east-2 --yes
```
