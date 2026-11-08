# Demo del Middleware RFHA-IES

Guía completa de la demo para la exposición: qué es, cómo levantarla **en local** y **en AWS**, cómo probarla, cómo explicar el código y qué hacer si algo falla.

Contenido
1. [Qué demuestra](#1-qué-demuestra)
2. [Levantar y probar en local](#2-levantar-y-probar-en-local)
3. [Levantar y probar en AWS](#3-levantar-y-probar-en-aws)
4. [Cómo probar los tres escenarios](#4-cómo-probar-los-tres-escenarios)
5. [Explicación del código](#5-explicación-del-código)
6. [Guion de la exposición](#6-guion-de-la-exposición)
7. [Si algo falla](#7-si-algo-falla)
8. [Por qué cumple con la exposición y con la propuesta](#8-por-qué-cumple-con-la-exposición-y-con-la-propuesta)

---

## 1. Qué demuestra

Un **middleware** que protege el historial académico de un estudiante. Un funcionario de otra universidad pide el historial a una única URL. El middleware revisa el **token de consentimiento** del estudiante y solo entonces entrega los datos.

```
Cliente (Thunder Client / IES consultante)
        │  GET /api/v1/federated/academic-history/20262678029
        │  Header: X-Student-Consent-Token: <JWT>
        ▼
┌──────────────────────────────────────────────┐
│ Middleware (FastAPI)                         │
│  1. ¿Hay token?            no → 403          │
│  2. ¿Firma válida y vigente? no → 403        │
│  3. ¿El token es de ese estudiante? no → 403 │
│  4. ¿Existe el estudiante? no → 404          │
│  5. Entrega el historial en JSON → 200       │
└──────────────────────────────────────────────┘
        ▼
 Datos simulados en memoria (representan DynamoDB)
```

| Escenario | Resultado esperado |
|---|---|
| Sin token | **403** |
| Token expirado (o inválido) | **403** |
| Token válido | **200** con el historial JSON |
| Estudiante inexistente con token válido para él | **404** |

Misma aplicación, dos formas de correrla:
- **Plan A, local:** en tu PC con `uvicorn`. No necesita internet ni AWS.
- **Plan B, AWS:** API Gateway + Lambda. Es el mismo código; solo cambia la URL.

Estudiante de la demo: `20262678029` (Brayan Acosta Parrado). Es el único con datos.

---

## 2. Levantar y probar en local

### 2.1 Forma rápida: un solo comando

Requisito: tener Python 3.11 o 3.12 instalado. El lanzador crea el entorno virtual, instala las dependencias, crea el `.env` con un secreto aleatorio, levanta la API, verifica los 3 escenarios e imprime los tokens.

**Windows (PowerShell), en la raíz del proyecto:**
```powershell
.\run-demo.ps1
```
Si PowerShell bloquea el script: `powershell -ExecutionPolicy Bypass -File .\run-demo.ps1`

**macOS / Linux:**
```bash
bash run-demo.sh
```

**Desde VS Code:** `Ctrl+Shift+P` → *Tasks: Run Task* → **Demo: levantar en local**.

**Cualquier sistema (con Python en el PATH):**
```bash
python scripts/run_demo.py
```
Opciones: `--port 8010` (otro puerto), `--no-check` (omite la verificación inicial) y `--once` (levanta, verifica y termina; lo usa el CI de GitHub).

Al terminar verás algo así:
```
[OK] Sin token: HTTP 403 (esperado 403)
[OK] Token expirado: HTTP 403 (esperado 403)
[OK] Token válido: HTTP 200 (esperado 200)
RESULTADO: TODO BIEN

TOKEN VÁLIDO (24 h):
eyJhbGciOi...
TOKEN EXPIRADO:
eyJhbGciOi...

DEMO LISTA
  API:            http://127.0.0.1:8000
  Documentación:  http://127.0.0.1:8000/docs
  Detener:        Ctrl+C
```
La primera vez tarda 1 a 2 minutos (instala dependencias). Las siguientes arrancan en segundos. **Deja esa terminal abierta mientras expones.**

### 2.2 Forma manual, paso a paso

Úsala si el lanzador falla o quieres explicar cada paso.

1. Abre una terminal en la raíz del proyecto.
2. Crea y activa el entorno virtual:
   - Windows: `py -3.12 -m venv .venv` y luego `.\.venv\Scripts\Activate.ps1`
   - macOS/Linux: `python3.12 -m venv .venv` y luego `source .venv/bin/activate`
3. Instala dependencias: `pip install -r demo/requirements-local.txt` (incluye `uvicorn`, que la Lambda no necesita)
4. Crea el secreto. Crea un archivo `.env` en la raíz con una línea:
   ```
   JWT_SECRET=pon-aqui-un-texto-aleatorio-de-mas-de-32-caracteres
   ```
   (o copia `.env.example` a `.env`). Si no creas `.env`, la demo usa un secreto de desarrollo inseguro; sirve en local, nunca en AWS.
5. Genera los tokens: `python scripts/generate_token.py`. Copia el **válido** y el **expirado**.
6. Levanta la API: `uvicorn demo.main:app --port 8000`
7. En otra terminal, verifica: `python scripts/check_demo.py http://127.0.0.1:8000` → debe decir `TODO BIEN`.

### 2.3 Interfaz web (la forma recomendada de exponer)

Con la demo en marcha, abre **http://127.0.0.1:8000** en el navegador.

1. En **Simular al estudiante** pulsa **Token válido**. El token aparece en el campo.
2. Pulsa **Consultar expediente**. La tarjeta *Validación del middleware* muestra los 4 pasos en verde y abajo aparece el expediente.
3. Pulsa **Sin token** y consulta de nuevo: se rechaza en el paso 1 con `HTTP 403`.
4. Pulsa **Token expirado** y consulta: se rechaza en el paso 2 con `HTTP 403`.
5. *Ver respuesta JSON* muestra la respuesta cruda. *Copiar como curl* copia el comando equivalente.

Los botones de **Simular al estudiante** solo existen en modo demostración, que el lanzador activa solo (`DEMO_MODE=1`). Representan el paso donde el estudiante da su consentimiento; en el proyecto final lo hará el propio estudiante (HU-04).

Qué incluye la interfaz: HTML semántico y accesible (etiquetas, foco visible, lector de pantalla, contraste AA), diseño adaptable a celular, modo claro y oscuro automático según el sistema, política de seguridad de contenido (CSP) estricta, sin librerías externas ni fuentes de terceros, y todo el contenido dinámico insertado como texto (sin `innerHTML`). Archivos: `demo/static/{index.html,styles.css,app.js,favicon.svg}`.

En AWS la misma página está en la URL raíz. Allí los botones de simulación vienen **apagados** (por seguridad): pega un token generado con `python scripts/generate_token.py`. Para ensayar con los botones, despliega con `DemoMode=1` agregándolo a `--parameter-overrides` (`"JwtSecret=<SECRETO>" "DemoMode=1"`) y vuelve a desplegar con `0` después, porque con `1` cualquiera que tenga la URL puede generar tokens.

#### Datos de prueba (6 estudiantes ficticios en 4 universidades)

Todos los datos son inventados. Cada código existe en la demo; cualquier otro código da 404.

| Código | Estudiante | Universidad (nodo) | Programa | Estado | Promedio | Créditos | Para qué sirve en la exposición |
|---|---|---|---|---|---|---|---|
| `20262678029` | Brayan Acosta Parrado | Universidad Distrital | Ingeniería en Telemática | Activo | 4,52 | 140 de 160 | Caso principal: éxito, rechazos y AWS. 8 asignaturas, una en curso. |
| `20251234501` | Laura Camila Ríos Herrera | Universidad Nacional | Ingeniería de Sistemas y Computación | Activo | 4,18 | 118 de 160 | **Homologación**: reprobó Cálculo Integral (2,6) y la repitió (3,4). 11 asignaturas. |
| `20241122002` | Andrés Felipe Moreno Castro | Pontificia Universidad Javeriana | Ingeniería Electrónica | **Graduado** | 4,05 | 168 de 168 | Egresado: muestra título (Ingeniero Electrónico) y fecha de grado (12 dic 2025). |
| `20231098763` | Valentina Torres Quintero | Universidad de los Andes | Economía | Activo | 4,62 | 90 de 140 | Promedio alto: candidata a beca o traslado. Dato de otro nodo. |
| `20221050914` | Juan Sebastián Pardo Gil | Universidad Distrital | Ingeniería Industrial | **Retirado** | 3,21 | 64 de 160 | Retirado: promedio bajo y materias repetidas (Física I, Probabilidad). |
| `20252345678` | María Fernanda Ospina Duarte | Universidad Nacional | Estadística | Activo | 3,88 | 52 de 150 | Primeros semestres con una asignatura en curso. |

Para probar un código inexistente usa, por ejemplo, `12345` (resultado 404).

En local, la lista desplegable **Estudiante de ejemplo** completa el código por ti. En AWS (modo demostración apagado) no aparece: escribe el código de la tabla.

#### Qué escribir en cada campo

| Campo | Qué poner | Para qué sirve |
|---|---|---|
| **Estudiante de ejemplo** (solo en modo demostración) | Elegir uno de la lista. | Completa el código del estudiante para no escribirlo. |
| **Código del estudiante** | `20262678029` (único estudiante con datos). Solo letras, números, guion y guion bajo, máximo 32 caracteres. | Identifica de quién se pide el historial. Va en la URL. |
| **Token de consentimiento** | Un token JWT. Con los botones de **Simular al estudiante** se llena solo. También puedes pegar uno de `python scripts/generate_token.py`, o dejarlo vacío. | Es la autorización firmada del estudiante. Va en el encabezado `X-Student-Consent-Token`. |
| Botón **Token válido** | Sin escribir nada más. | Genera un token vigente 24 h **para el código que tengas escrito en ese momento**. |
| Botón **Token expirado** | Sin escribir nada más. | Genera un token ya vencido, para el código escrito. |
| Botón **Sin token** | Sin escribir nada más. | Borra el campo del token. |
| **Consultar expediente** | Pulsarlo al final. | Envía la solicitud y muestra el resultado. |

#### Casos de prueba (interfaz web)

Antes de cada caso, recarga la página o revisa los campos. Pulsa **Consultar expediente** al final de cada uno.

| # | Caso | Código del estudiante | Token (qué hacer) | Resultado esperado | Pasos de validación |
|---|---|---|---|---|---|
| 1 | **Éxito** | `20262678029` | Pulsa **Token válido** | **HTTP 200**. «Acceso concedido». Aparece Brayan Acosta Parrado (Activo), promedio 4,52, 140 de 160 créditos y 8 asignaturas, la última «En curso». | Los 4 en verde |
| 2 | **Sin token** | `20262678029` | Pulsa **Sin token** (campo vacío) | **HTTP 403**. «ACCESO DENEGADO: falta el token de consentimiento del estudiante.» | Paso 1 rechazado; 2, 3 y 4 omitidos |
| 3 | **Token expirado** | `20262678029` | Pulsa **Token expirado** | **HTTP 403**. «El token de consentimiento ha expirado.» | Paso 1 aprobado; paso 2 rechazado; 3 y 4 omitidos |
| 4 | **Token con firma alterada** | `20262678029` | Pulsa **Token válido** y luego cambia o borra una letra del final del token | **HTTP 403**. «ACCESO DENEGADO: token de consentimiento inválido.» | Paso 2 rechazado |
| 5 | **Texto que no es un token** | `20262678029` | Escribe `esto-no-es-un-jwt` | **HTTP 403**. «…token de consentimiento inválido.» | Paso 2 rechazado |
| 6 | **Token de otro estudiante** | Escribe `99999999`, pulsa **Token válido**, y **vuelve a escribir** `20262678029` | Deja el token generado | **HTTP 403**. «ACCESO DENEGADO: el token no autoriza a este estudiante.» | Pasos 1 y 2 aprobados; paso 3 rechazado |
| 7 | **Estudiante inexistente** | `12345` | Pulsa **Token válido** (con `12345` ya escrito) | **HTTP 404**. «Estudiante no encontrado en la red federada.» | Pasos 1, 2 y 3 aprobados; paso 4 rechazado |
| 8 | **Código no válido** | `abc def` o `<script>` o vacío | Cualquiera | No se envía nada. Mensaje rojo bajo el campo: «Escribe un código válido: solo letras, números, guion o guion bajo (máximo 32).» | Sin cambios |
| 9 | **Servidor apagado** | `20262678029` | Cualquiera | Insignia «Sin conexión» y «No se pudo conectar con el servidor. Verifica que la API esté en ejecución.» Para probarlo: detén la demo con `Ctrl+C` y pulsa Consultar. | Sin cambios |
| 10 | **Ver JSON y curl** | `20262678029` | Haz el caso 1 | Abre *Ver respuesta JSON* para ver la respuesta cruda. Pulsa *Copiar como curl* y pégalo en una terminal: da el mismo resultado. | — |

Nota del caso 6 y 7: **Token válido** firma el token con el código que esté escrito al pulsar el botón. Por eso en el caso 6 se cambia el código después de generar el token.

#### Casos con los demás estudiantes

Para cada uno: elígelo en **Estudiante de ejemplo** (o escribe su código), pulsa **Token válido** y **Consultar expediente**.

| # | Estudiante | Qué observar | Resultado esperado |
|---|---|---|---|
| 11 | **Laura Ríos** `20251234501` | Dos filas de «Cálculo Integral» (2024-2 reprobada con 2,6 y 2025-1 aprobada con 3,4). En *Apoyo a la homologación* deja la nota mínima en 3,5 y luego pásala a 4,0. | HTTP 200. Con 3,5: 8 de 9 asignaturas aprobadas son candidatas (25 créditos); con 4,0: 7 de 9 (21 créditos). Cálculo Integral (3,4) no es candidata con una nota mínima de 3,5 o más. La fila reprobada sale en rojo y «Reprobada»; la de 2026-2 sale «En curso». |
| 12 | **Andrés Moreno** `20241122002` | Aparecen *Título* y *Fecha de grado*. Estado «Graduado», créditos 168 de 168 (100 %). | HTTP 200. 6 asignaturas, todas aprobadas. |
| 13 | **Valentina Torres** `20231098763` | Promedio 4,62 y notas altas; datos de la Universidad de los Andes. | HTTP 200. Con nota mínima 4,5: 7 de 8 aprobadas son candidatas (22 créditos); solo Econometría I (4,4) queda fuera. |
| 14 | **Juan Pardo** `20221050914` | Estado «Retirado». Física I y Probabilidad reprobadas; Física I repetida y aprobada (3,4). | HTTP 200. Con nota mínima 3,5: solo 2 de 6 asignaturas aprobadas son candidatas (Química General 3,5 y Dibujo Técnico 3,8): 5 créditos. |
| 15 | **María Ospina** `20252345678` | Primeros semestres, 52 de 150 créditos (35 %) y una asignatura en curso. | HTTP 200. Con nota mínima 3,5: 8 de 8 aprobadas son candidatas (26 créditos). Con 4,0: 4 de 8 (Introducción 4,2; Lógica 4,0; Programación en R 4,4; Inferencia 4,1) y 12 créditos. |
| 16 | **Otro nodo, mismo servicio** | Consulta a Brayan (Distrital), Laura (Nacional) y Valentina (Andes) seguidas. | Mismo formato y mismos 4 pasos, sin cambiar nada: transparencia de ubicación. |

Cálculos de referencia de los casos 11 a 15 (nota mínima = «3,5», salvo que se indique): se cuentan solo asignaturas **aprobadas** con nota mayor o igual a la mínima.

#### Casos en AWS (sin botones de simulación)

En AWS los botones no aparecen. Genera los tokens en tu PC con el **mismo `JWT_SECRET`** que tiene la Lambda y pégalos en el campo:

| Caso | Comando para generar el token | Qué pegar |
|---|---|---|
| 1, 2, 3 | `python scripts/generate_token.py` | Token válido → caso 1. Token expirado → caso 3. Campo vacío → caso 2. |
| 6 (otro estudiante) | `python scripts/generate_token.py 99999999` | El token **válido** impreso; consulta el código `20262678029`. |
| 7 (inexistente) | `python scripts/generate_token.py 12345` | El token **válido** impreso; consulta el código `12345`. |
| 4 y 5 | No necesita comando | Altera una letra de un token válido, o escribe `esto-no-es-un-jwt`. |

Si ves 403 con un token que debería ser válido, casi siempre es porque el secreto de tu `.env` no coincide con el desplegado (ver sección 7).

#### Casos en Swagger (`/docs`) y Thunder Client

- **Swagger** (`http://127.0.0.1:8000/docs`): abre `GET /api/v1/federated/academic-history/{student_id}` → *Try it out* → en `student_id` escribe `20262678029` y en `X-Student-Consent-Token` pega el token (déjalo vacío para el caso 2) → *Execute*. Mira el *Code* de respuesta y el *Response body*.
- **Thunder Client**: entorno **Local** (o **AWS**), variables `validToken` y `expiredToken` con los tokens del script. Request `1. Sin token` (403), `2. Token valido` (200), `3. Token expirado` (403). Para los casos 4 a 7 duplica la request 2 y cambia el token o el código en la URL.

### 2.4 Probar en local con Thunder Client

1. Abre la extensión **Thunder Client** (icono del rayo).
2. Pestaña *Collections* → **RFHA-IES** → carpeta **Demo** (tres requests).
3. Pestaña *Env* → selecciona **Local**. Pega los tokens en `validToken` y `expiredToken`.
4. Ejecuta en orden: `1. Sin token (403)`, `3. Token expirado (403)`, `2. Token valido (200)`.

Si no aparece la colección, usa `curl` (sección 4).

### 2.5 Documentación Swagger

Abre `http://127.0.0.1:8000/docs`. Es la documentación de la API generada automáticamente. Pulsa *Try it out* en el endpoint, escribe el `student_id` `20262678029` y el token en el campo del header.

---

## 3. Levantar y probar en AWS

Esta parte la hace **quien administra la cuenta AWS** (no necesita entender el código). Esta sección es completa: no hace falta abrir ningún otro documento.

### 3.0 Resumen

| | |
|---|---|
| **Qué se despliega** | Un stack de CloudFormation llamado **`rfha-demo`** con: 1 función Lambda (`rfha-demo`, Python 3.11, 256 MB), 1 API Gateway tipo HTTP API y 1 grupo de logs de CloudWatch con retención de 7 días. **No usa DynamoDB ni S3 propios** (SAM crea un bucket interno para subir el código). |
| **Qué entrega** | Una URL pública `https://xxxxxxxx.execute-api.us-east-1.amazonaws.com`. Al abrirla en el navegador aparece la interfaz de la demo, y la API responde igual que en local. |
| **Qué necesita de Brayan** | El **secreto JWT** (texto de 32 caracteres o más). Se pasa al desplegar. |
| **Región** | `us-east-1` (Virginia del Norte). |
| **Costo** | USD 0 dentro del Free Tier. Con el plan *Free* de cuentas nuevas no se cobra nada; con una cuenta antigua el consumo de esta demo es insignificante. El API tiene un límite de 20 peticiones por segundo para evitar abusos. |
| **Tiempo** | 30 a 45 minutos la primera vez; menos de 5 minutos al repetir. |
| **Quién hace qué** | **Compañero de AWS:** pasos 1 a 10. **Brayan:** entrega el secreto (paso 7) y prueba al final (paso 11). |

### 3.1 Qué necesita tener el compañero
- Un computador con **Windows y PowerShell** (los comandos de abajo son para PowerShell), con internet.
- Una **tarjeta** con pagos internacionales para crear la cuenta AWS (AWS la pide aunque no cobre).
- Permiso para instalar programas.

### 3.2 Paso a paso

#### Paso 1. Crear o verificar la cuenta AWS
- **Dónde:** navegador, https://aws.amazon.com
- **Pasos:**
  1. Pulsa *Crear una cuenta de AWS* (o entra con la cuenta existente).
  2. Si la cuenta es nueva, cuando pregunte por el plan elige **Free account plan** (plan gratuito). No elijas el *Paid plan*.
  3. Entra a la consola, abre *Billing and Cost Management* → *Free Tier* y comprueba que aparece el plan y el saldo de créditos.
  4. Arriba a la derecha, en el selector de región, elige **US East (N. Virginia) us-east-1**.
- **Resultado esperado:** ves el panel de Free Tier y la región `us-east-1`.
- **Si falla:** la tarjeta se rechaza → prueba otra con pagos internacionales habilitados. Cuenta antigua sin plan Free → sigue igual y no te saltes el paso 2.

#### Paso 2. Alerta de presupuesto de USD 0.01
- **Dónde:** consola web → *Billing and Cost Management* → *Budgets*.
- **Pasos:**
  1. *Create budget* → *Use a template (simplified)* → **Zero spend budget**.
  2. Escribe los correos del compañero y de Brayan.
  3. *Create budget*.
- **Resultado esperado:** aparece «My Zero-Spend Budget» con estado activo; AWS avisará por correo ante cualquier gasto.
- **Si falla:** si no aparece la plantilla, crea un *Customized (advanced)* → *Cost budget* mensual de USD 0.01.

#### Paso 3. Crear un usuario IAM para desplegar (no usar la cuenta raíz)
- **Dónde:** consola web → *IAM* → *Users*.
- **Pasos:**
  1. *Create user* → nombre `rfha-deployer` → *Next*.
  2. *Attach policies directly* y marca estas **6 políticas**:
     `AWSCloudFormationFullAccess`, `AWSLambda_FullAccess`, `AmazonAPIGatewayAdministrator`, `AmazonS3FullAccess`, `CloudWatchLogsFullAccess`, `IAMFullAccess`.
  3. *Create user*.
  4. Abre el usuario → pestaña *Security credentials* → *Create access key* → caso de uso **Command Line Interface (CLI)** → confirma → *Create access key*.
  5. Copia el **Access key ID** y el **Secret access key** a un gestor de contraseñas (el secreto solo se muestra una vez).
- **Resultado esperado:** tienes el par de claves del usuario `rfha-deployer`.
- **Si falla:** si luego el despliegue da `AccessDenied`, falta alguna de las 6 políticas. **Nunca** subas estas claves a git ni las pegues en chats.

#### Paso 4. Instalar las herramientas
- **Dónde:** PowerShell (abre una nueva).
- **Pasos:**
  ```powershell
  winget install Amazon.AWSCLI
  winget install Amazon.SAM-CLI
  winget install Python.Python.3.11
  winget install Git.Git
  ```
  Cierra PowerShell y ábrelo de nuevo. Comprueba:
  ```powershell
  aws --version
  sam --version
  py -3.11 --version
  git --version
  ```
- **Resultado esperado:** los cuatro comandos muestran una versión (`py -3.11` debe decir `Python 3.11.x`).
- **Si falla:** `comando no encontrado` → no cerraste y reabriste PowerShell. Sin `winget` → descarga los instaladores desde las páginas oficiales de AWS CLI, AWS SAM CLI, python.org y git-scm.com. **Python 3.11 es necesario**: `sam build` debe encontrar la misma versión que usa la Lambda.

#### Paso 5. Conectar la terminal con la cuenta
- **Dónde:** PowerShell.
- **Pasos:**
  ```powershell
  aws configure
  ```
  Responde: `AWS Access Key ID` → la del paso 3; `AWS Secret Access Key` → la del paso 3; `Default region name` → `us-east-1`; `Default output format` → `json`. Luego:
  ```powershell
  aws sts get-caller-identity
  ```
- **Resultado esperado:** devuelve un JSON con `Account` (12 dígitos) y `Arn` que termina en `user/rfha-deployer`.
- **Si falla:** `InvalidClientTokenId` o `SignatureDoesNotMatch` → clave mal copiada; repite `aws configure`.

#### Paso 6. Descargar el código
- **Dónde:** PowerShell.
- **Pasos:**
  ```powershell
  git clone https://github.com/BrayanBMC/RFHA-IES_SD_TGS.git
  cd RFHA-IES_SD_TGS
  ```
  Si Brayan indica que lo último está en la rama `dev` (todavía no se hizo el merge a `main`), añade: `git checkout dev`.
- **Resultado esperado:** existe la carpeta `RFHA-IES_SD_TGS` con la subcarpeta `demo` que contiene `template.yaml` y `main.py`. Compruébalo con `dir demo`.
- **Si falla:** `repository not found` → pide a Brayan que te dé acceso al repositorio.

#### Paso 7. Obtener el secreto JWT
- **Quién:** Brayan lo genera y se lo pasa al compañero **por un canal privado** (mensaje directo, no un grupo público).
- **Cómo se genera** (cualquier PC con Python):
  ```powershell
  py -3.11 -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
  Imprime un texto de unos 64 caracteres, por ejemplo `kQ3v...`. Ese texto es el **secreto**.
- **Para el compañero:** guárdalo en una variable de la terminal (solo vive mientras la terminal esté abierta):
  ```powershell
  $secreto = "PEGA_AQUI_EL_SECRETO"
  ```
- **Reglas:** mínimo 32 caracteres; Brayan debe guardar el mismo valor en su archivo `.env` como `JWT_SECRET=...` para poder generar tokens que la Lambda acepte. No se sube a git.

#### Paso 8. Construir el paquete
- **Dónde:** PowerShell, dentro de la carpeta `RFHA-IES_SD_TGS`.
- **Comando:**
  ```powershell
  sam build --template-file demo/template.yaml
  ```
- **Resultado esperado:** al final dice `Build Succeeded` y crea la carpeta `.aws-sam\build`.
- **Si falla:**
  - `Binary validation failed for python` → no está Python 3.11 en el PATH: repite el paso 4 y reabre PowerShell.
  - `template.yaml not found` → no estás en la carpeta raíz del proyecto.

#### Paso 9. Desplegar
- **Dónde:** misma terminal (con `$secreto` definido en el paso 7).
- **Comando:**
  ```powershell
  sam deploy --template-file .aws-sam/build/template.yaml --stack-name rfha-demo --resolve-s3 --capabilities CAPABILITY_IAM --region us-east-1 --no-confirm-changeset --no-fail-on-empty-changeset --parameter-overrides "JwtSecret=$secreto" "DemoMode=0"
  ```
  - `DemoMode=0` es lo normal y seguro: en la interfaz **no** aparecen los botones que generan tokens de prueba.
  - `DemoMode=1` es solo para **ensayar con los botones** de la interfaz. Con `1`, cualquiera que conozca la URL puede generar tokens y saltarse la protección; vuelve a desplegar con `0` después.
- **Resultado esperado:** tarda 2 a 4 minutos y termina con `Successfully created/updated stack - rfha-demo in us-east-1`. En la sección *Outputs* aparece:
  ```
  Key         ApiUrl
  Description URL base para Thunder Client (variable baseUrl del entorno AWS)
  Value       https://abc123xyz.execute-api.us-east-1.amazonaws.com
  ```
- **Si falla:**
  - `AccessDenied` / `not authorized` → falta una política del paso 3.
  - `Parameter JwtSecret ... length` → el secreto tiene menos de 32 caracteres.
  - `ROLLBACK_COMPLETE` → mira el motivo en consola web → CloudFormation → stack `rfha-demo` → pestaña *Events*. Para reintentar, borra el stack fallido (`sam delete --stack-name rfha-demo --region us-east-1`) y repite el paso 9.
  - `The security token included in the request is invalid` → repite el paso 5.

#### Paso 10. Copiar la URL y comprobar que responde
- **Dónde:** PowerShell y navegador.
- **Pasos:**
  1. Copia el `Value` de `ApiUrl`. Si se perdió:
     ```powershell
     aws cloudformation describe-stacks --stack-name rfha-demo --region us-east-1 --query "Stacks[0].Outputs"
     ```
  2. Abre la URL en el navegador: debe cargar la página **«Consulta federada de historial académico»**.
  3. Primera petición a la API (calienta la Lambda):
     ```powershell
     curl.exe -i https://abc123xyz.execute-api.us-east-1.amazonaws.com/api/v1/federated/academic-history/20262678029
     ```
- **Resultado esperado:** la página carga y el `curl` devuelve `HTTP/1.1 403` con el texto `ACCESO DENEGADO: falta el token de consentimiento del estudiante.` El 403 es **correcto**: significa que la Lambda y el API Gateway funcionan y que la protección está activa.
- **Si falla:**
  - `{"message":"Not Found"}` → la URL está incompleta o con una ruta mal escrita.
  - `{"message":"Internal Server Error"}` → error dentro de la Lambda: mira los logs (3.4).
  - La primera petición tarda 1 a 3 segundos: es el arranque en frío, normal.

#### Paso 11. Prueba completa (con el secreto)
- **Quién:** Brayan, o el compañero si instala PyJWT.
- **Dónde:** PowerShell en la carpeta del proyecto.
- **Pasos:**
  ```powershell
  py -3.11 -m pip install PyJWT
  $env:JWT_SECRET = $secreto
  py -3.11 scripts/check_demo.py https://abc123xyz.execute-api.us-east-1.amazonaws.com
  ```
- **Resultado esperado:**
  ```
  [OK] Sin token: HTTP 403 (esperado 403)
  [OK] Token expirado: HTTP 403 (esperado 403)
  [OK] Token válido: HTTP 200 (esperado 200)
  RESULTADO: TODO BIEN
  ```
- **Si falla:** `Token válido: HTTP 403` → el secreto de esta terminal no es el mismo que se desplegó; repite el paso 7 y el paso 9.

#### Paso 12. Entregar a Brayan
Envía a Brayan **la URL** (`ApiUrl`) y confirma si el despliegue fue con `DemoMode=0` o `1`. Con esa URL Brayan:
1. Abre la URL en el navegador para exponer la interfaz.
2. En Thunder Client, entorno **AWS**, cambia `baseUrl` por la URL (sin barra final).
3. Genera los tokens en su PC con `python scripts/generate_token.py` (mismo `JWT_SECRET` en su `.env`).

### 3.3 Despliegue alternativo desde GitHub (opcional)
Evita instalar SAM en el PC del compañero. En el repositorio de GitHub:
1. *Settings* → *Secrets and variables* → *Actions* → *New repository secret*. Crea tres: `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY` (las claves del paso 3) y `DEMO_JWT_SECRET` (el secreto del paso 7).
2. Pestaña *Actions* → workflow **CD demo (manual)** → *Run workflow*.
3. Al terminar, la URL se consulta con el comando `aws cloudformation describe-stacks` del paso 10, o en la consola web de CloudFormation → stack `rfha-demo` → *Outputs*.
El workflow nunca corre solo, y despliega con `DemoMode=0`.

### 3.4 Ver los logs si algo falla
```powershell
sam logs --stack-name rfha-demo --region us-east-1
```
También en la consola: *CloudWatch* → *Log groups* → `/aws/lambda/rfha-demo`.

### 3.5 Actualizar la demo (si Brayan cambia el código)
Repite desde el paso 8 (`git pull`, `sam build`, `sam deploy` con el mismo secreto). La URL no cambia.

### 3.6 Borrar todo al terminar (evita costos)
```powershell
sam delete --stack-name rfha-demo --region us-east-1
```
Responde `y` a las preguntas. Después, en la consola → *S3*, borra el bucket que empieza por `aws-sam-cli-managed-default` si ya no vas a desplegar más. Finalmente, en *IAM*, desactiva o elimina la access key del usuario `rfha-deployer`.

---

## 4. Cómo probar los tres escenarios

Reemplaza `BASE` por `http://127.0.0.1:8000` (local) o la URL de AWS. Usa los tokens de `python scripts/generate_token.py`.

**macOS/Linux/Git Bash:**
```bash
BASE=http://127.0.0.1:8000
URL=$BASE/api/v1/federated/academic-history/20262678029

curl -i $URL                                                  # 1. sin token  → 403
curl -i -H "X-Student-Consent-Token: <EXPIRADO>" $URL         # 2. expirado   → 403
curl -i -H "X-Student-Consent-Token: <VALIDO>" $URL           # 3. válido     → 200
```

**Windows PowerShell** (usa `curl.exe`, porque `curl` es otro alias):
```powershell
$URL = "http://127.0.0.1:8000/api/v1/federated/academic-history/20262678029"
curl.exe -i $URL
curl.exe -i -H "X-Student-Consent-Token: <EXPIRADO>" $URL
curl.exe -i -H "X-Student-Consent-Token: <VALIDO>" $URL
```

Respuestas esperadas:

```json
// 1. Sin token → 403
{"detail": "ACCESO DENEGADO: falta el token de consentimiento del estudiante."}

// 2. Expirado → 403
{"detail": "El token de consentimiento ha expirado."}

// 3. Válido → 200
{
  "status": "SUCCESS",
  "middleware_layer": "AWS API Gateway + AWS Lambda",
  "transparency_verified": true,
  "data": {
    "student_id": "20262678029",
    "full_name": "Brayan Acosta Parrado",
    "university": "Universidad Distrital Francisco José de Caldas",
    "program": "Ingeniería en Telemática",
    "gpa": 4.52,
    "courses": [
      {"code": "165-301", "name": "Sistemas Distribuidos", "grade": 4.8},
      {"code": "165-302", "name": "Teoría General de Sistemas", "grade": 4.5}
    ]
  }
}
```

Pruebas extra opcionales: cambiar una letra del token (403 firma inválida); pedir otro `student_id` con el token de `20262678029` (403, el token no autoriza a otro estudiante).

---

## 5. Explicación del código

### 5.1 Mapa de archivos de la demo

| Archivo | Para qué sirve |
|---|---|
| `demo/main.py` | **Toda la API.** Validación del token, datos simulados, endpoint, y sirve la interfaz web. |
| `demo/students.py` | Los 6 estudiantes ficticios (datos de prueba) con sus asignaturas. Se editan aquí. |
| `demo/static/` | Interfaz web: `index.html`, `styles.css`, `app.js`, `favicon.svg`. |
| `demo/tests/test_demo_data.py` | Pruebas de los datos de prueba (6 estudiantes, estados coherentes con las notas). |
| `demo/tests/test_demo_frontend.py` | Pruebas de la interfaz y del modo demostración. |
| `demo/requirements.txt` | Librerías que necesita la Lambda en AWS. |
| `demo/requirements-local.txt` | Las mismas más `uvicorn`, para correr en local. |
| `demo/template.yaml` | Plantilla AWS SAM: crea la Lambda y el API Gateway. |
| `demo/tests/test_demo_api.py` | Pruebas automáticas (las corre GitHub en cada push). |
| `scripts/generate_token.py` | Crea tokens JWT válidos y expirados. |
| `scripts/check_demo.py` | Prueba los 3 escenarios contra cualquier URL. |
| `scripts/run_demo.py` | Lanzador de un comando para el modo local. |
| `run-demo.ps1` / `run-demo.sh` | Atajos que buscan Python y llaman al lanzador. |
| `thunder-tests/` | Requests y entornos de Thunder Client. |
| `.github/workflows/ci.yml` | Corre las pruebas en GitHub. |
| `.github/workflows/cd-demo.yml` | Despliegue manual a AWS desde GitHub. |

### 5.2 `demo/main.py` por partes

**Carga de configuración**
```python
def _load_dotenv(): ...
_load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-insecure-secret-do-not-use-in-aws")
```
Lee el archivo `.env` (solo en local) y obtiene el secreto con el que se firman y validan los tokens. En AWS no hay `.env`: el secreto llega como variable de entorno de la Lambda. El valor por defecto existe solo para que la demo arranque en local sin configurar nada.

**La aplicación**
```python
app = FastAPI(title=..., description=...)
```
FastAPI crea el servidor web y la documentación en `/docs` automáticamente.

**Datos simulados**
```python
MOCK_DYNAMODB_NODES = { "20262678029": { ... } }
```
Un diccionario en memoria que hace de base de datos. Representa lo que luego será DynamoDB en cada nodo universitario. Por eso la demo no necesita ningún servicio de base de datos.

**Validación del token: `verify_student_token(token, student_id)`**

| Paso | Código | Resultado si falla |
|---|---|---|
| 1. ¿Llegó el token? | `if not token` | 403 "falta el token" |
| 2. ¿Firma y vigencia? | `jwt.decode(..., algorithms=["HS256"], options={"require": ["exp"]})` | 403 "expirado" o "inválido" |
| 3. ¿Es de este estudiante? | `payload.get("student_id") != student_id` | 403 "no autoriza a este estudiante" |

- `HS256` es la firma con clave secreta compartida: solo quien conoce `JWT_SECRET` puede crear un token que pase.
- PyJWT revisa solo la fecha de expiración (`exp`). `require: ["exp"]` rechaza tokens sin fecha, que serían eternos.
- Se separa `ExpiredSignatureError` de `InvalidTokenError` para dar un mensaje distinto a cada caso. Ambos terminan en 403.

**El endpoint**
```python
@app.get("/api/v1/federated/academic-history/{student_id}")
async def get_academic_history(student_id: str, x_student_consent_token: str | None = Header(default=None, alias="X-Student-Consent-Token")):
```
- `{student_id}` viene de la URL.
- El header es **opcional a propósito** (`default=None`). Si fuera obligatorio, FastAPI respondería **422** cuando falta, y lo correcto para seguridad es **403**. Así validamos nosotros y devolvemos 403.
- Orden: primero se valida el token y **después** se busca el dato. Sin consentimiento, el middleware ni toca la "base de datos" (por eso un estudiante inexistente sin token da 403 y no 404; no revela quién existe).
- Si pasa la validación y el estudiante no está: 404.
- Si todo está bien: JSON con `status`, `middleware_layer`, `transparency_verified` y `data`.

**Adaptador para AWS**
```python
handler = Mangum(app, lifespan="off")
```
API Gateway no habla "web" directamente con FastAPI; envía eventos a Lambda. **Mangum** traduce el evento de API Gateway a una petición normal y la respuesta de vuelta. Es una sola línea, y el resto del código es idéntico en local y en AWS. En AWS, el `Handler: main.handler` de la plantilla apunta aquí.

### 5.3 `scripts/generate_token.py`
Crea un JWT con tres datos: `student_id` (de quién es el consentimiento), `iat` (cuándo se emitió) y `exp` (cuándo vence), firmado con `JWT_SECRET`. Genera dos: uno que dura 24 h y otro que ya venció hace una hora (`expires_in=-3600`) para la demo del escenario 2. Reemplaza a jwt.io.

### 5.4 `scripts/check_demo.py`
Hace tres peticiones HTTP con la biblioteca estándar (sin instalar nada) y compara el código recibido con el esperado. Sirve igual para `http://127.0.0.1:8000` y para la URL de AWS; sale con error si algo no coincide.

### 5.5 `scripts/run_demo.py`
Automatiza lo que se haría a mano: crea `.venv`, instala dependencias si cambió el hash de `demo/requirements-local.txt`, crea `.env`, lanza `uvicorn` como subproceso, espera a que responda, ejecuta `check_demo.py`, imprime los tokens y se queda esperando hasta `Ctrl+C`, momento en que apaga el servidor.

### 5.6 `demo/template.yaml` (AWS SAM)

| Recurso | Qué crea |
|---|---|
| `JwtSecret` (parámetro, `NoEcho`) | Recibe el secreto al desplegar; no se muestra en consola. Mínimo 32 caracteres. |
| `DemoApi` (`HttpApi`) | El API Gateway. Límite de 20 peticiones/s (ráfaga 50) para evitar abusos y costos. |
| `DemoFunction` | La Lambda `rfha-demo`: Python 3.11, 256 MB, 10 s. `JWT_SECRET` se pasa como variable de entorno. |
| Evento `Any` en `/{proxy+}` | Todas las rutas y métodos llegan a la misma Lambda; FastAPI decide qué responder. |
| `DemoLogGroup` | Logs en CloudWatch con retención de 7 días (evita costos ocultos). |
| `Outputs.ApiUrl` | Imprime la URL pública al terminar. |

### 5.7 Pruebas automáticas (`demo/tests/test_demo_api.py`)
Cubren: sin token (403 y no 422), válido (200), expirado, firma incorrecta, texto que no es JWT, token sin `exp`, token de otro estudiante, estudiante inexistente (404) y que exista el `handler`. GitHub las ejecuta en cada push a `dev` (`.github/workflows/ci.yml`).

### 5.8 Conceptos de clase que muestra
- **Middleware:** intermediario único que oculta dónde y cómo se guardan los datos.
- **Transparencia de acceso:** todas las IES consultan con la misma API REST y JSON.
- **Transparencia de ubicación:** el cliente solo conoce una URL, no el servidor ni la base de datos.
- **Seguridad y privacidad:** sin consentimiento firmado, el middleware corta antes de tocar los datos.
- **Serverless:** en AWS no hay servidores que administrar; la Lambda se ejecuta solo cuando llega una petición.

---

## 6. Guion de la exposición

Tiempo total: **12 a 14 minutos** (mínimo 10 minutos si se omiten los bloques marcados como opcionales). La demo usa 6 estudiantes ficticios de 4 universidades, así que hay material de sobra.

**Lista de verificación 10 minutos antes:**
- [ ] Plan A: `.\run-demo.cmd` ejecutándose y la página abierta en `http://127.0.0.1:8000`.
- [ ] Los 3 escenarios probados en la interfaz (casos 1, 2 y 3 de la sección 2.3).
- [ ] Plan B: URL de AWS abierta en el navegador y una petición de calentamiento hecha (paso 10 de la sección 3.2).
- [ ] Un token válido y uno expirado generados el mismo día (`python scripts/generate_token.py`).
- [ ] Thunder Client con el selector de entorno visible (`Local` y `AWS`).

### Guion minuto a minuto

| Minutos | Bloque | Qué haces en la pantalla | Qué dices |
|---|---|---|---|
| 0:00 a 1:30 | **1. Apertura y problema** | Diapositiva o la página principal de la demo. | Cada universidad guarda el historial académico en su propia base de datos, aislada de las demás. Una homologación o una beca toma de 15 a 45 días hábiles por certificados en papel. RFHA-IES conecta las universidades sin centralizar los datos. |
| 1:30 a 3:00 | **2. Qué es el middleware** | Muestra el esquema de la sección 1 de este documento y abre `/docs` (Swagger) unos segundos. | El middleware es un intermediario con tres funciones: transportista (una sola URL), seguridad (valida el consentimiento antes de tocar los datos) y traductor (entrega siempre el mismo JSON). El contrato REST se documenta solo en `/docs`. |
| 3:00 a 4:30 | **3. Caso exitoso** | Estudiante de ejemplo: **Brayan Acosta Parrado**. Pulsa **Token válido** y **Consultar expediente**. | Aparecen los 4 pasos en verde: token presente, firma y vigencia, titular y búsqueda. Muestra el expediente: estado académico, promedio, créditos (140 de 160) y las asignaturas por semestre. Abre *Ver respuesta JSON*. |
| 4:30 a 6:00 | **4. Rechazos** | Mismo estudiante. **Sin token** → consulta. **Token expirado** → consulta. **Token válido** y cambia una letra → consulta. | Los tres terminan en 403 y se detienen en un paso distinto. El middleware corta antes de tocar los datos: sin consentimiento vigente y firmado no hay acceso. |
| 6:00 a 7:00 | **5. Privacidad: el token es de una persona** | Elige a **Laura Ríos**, pulsa **Token válido**, luego elige a **Valentina Torres** (sin generar otro token) y consulta. | El paso 3 rechaza: el consentimiento de Laura no sirve para ver a Valentina. Cada estudiante decide quién ve su información. |
| 7:00 a 8:30 | **6. Federación: transparencia de ubicación** | Consulta con su propio token a **Laura** (Nacional), **Andrés Moreno** (Javeriana) y **Valentina** (Andes). | Tres universidades distintas, una sola URL, mismo formato. El cliente no sabe dónde viven los datos. Cada nodo tendrá su propia tabla en DynamoDB; la API no cambia. |
| 8:30 a 10:00 | **7. Caso de uso: homologación** | **Laura**: tiene Cálculo Integral reprobada (2,6) y repetida (3,4). Cambia la **Nota mínima aceptada** de 3,5 a 4,0 y observa cuántos créditos son candidatos. | La universidad que recibe fija su criterio (por ejemplo, nota mínima). Pasa de semanas a segundos. Se ven las asignaturas candidatas resaltadas y el total de créditos. |
| 10:00 a 10:45 | **8. Más estados académicos** *(opcional)* | **Andrés Moreno** (graduado): título y fecha de grado. **Juan Pardo** (retirado, promedio 3,21): materias repetidas. | El mismo servicio atiende egresados, activos y retirados. |
| 10:45 a 11:15 | **9. Estudiante inexistente** *(opcional)* | Escribe el código `12345`, **Token válido**, consulta. | 404: el token es válido pero el estudiante no existe en la red. Se diferencia un acceso denegado de un dato inexistente. |
| 11:15 a 12:15 | **10. Mismo código en AWS** | Abre la URL de AWS en otra pestaña (o cambia el entorno de Thunder Client a **AWS**). Repite el caso 3. | Es el mismo código sobre API Gateway y Lambda, sin servidores. Cambió la URL, no el comportamiento. Escala solo y entra en el Free Tier. |
| 12:15 a 13:15 | **11. Avance del proyecto final** *(opcional)* | En otra terminal: `.\run-app.cmd` y abre `http://127.0.0.1:8001/registro-nodo`. Registra una universidad. | HU-01 ya está terminada: una universidad solicita su alta y queda pendiente de aprobación. Siguen HU-02 a HU-10. |
| 13:15 a 14:00 | **12. Cierre** | Diapositiva final. | Transparencia de acceso y de ubicación demostradas, seguridad por consentimiento, serverless. Pendiente: failover a réplica, auditoría y portal del estudiante. |

**Para recortar a 10 minutos:** omite los bloques 8, 9 y 11 (opcionales) y resume el bloque 5. **Si sobra tiempo:** repite el bloque 6 con el cuarto estudiante y muestra el `curl` con *Copiar como curl*.

### Preguntas probables de los docentes

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué un token JWT? | Está firmado: si alguien lo altera se rechaza (caso 4), lleva fecha de vencimiento y no necesita consultar una base de datos para validarlo. |
| ¿Quién genera el token? | En la demo, los botones de simulación. En el proyecto final lo genera el propio estudiante (HU-04) y puede revocarlo (HU-05). |
| ¿Dónde está el secreto? | En una variable de entorno de la Lambda, nunca en el código ni en git. |
| ¿Qué pasa si un nodo se cae? | Se prevé un failover a una réplica con el encabezado `X-Data-Source` (HU-08). Todavía no está construido. |
| ¿Quedan registros de quién consultó? | Está previsto en una bitácora de solo inserción (HU-09). Todavía no está construida. |
| ¿Por qué serverless? | Sin servidores que administrar, escala sola de 0 a muchas peticiones y entra en el Free Tier. |
| ¿Son datos reales? | No. Los 6 estudiantes y sus notas son ficticios. |
| ¿Cómo se relaciona con Teoría General de Sistemas? | Es un sistema abierto con entradas (petición y token), proceso (validación), salidas (expediente) y retroalimentación (el rechazo y el failover); la sinergia es que la red vale más que cada universidad aislada. |

---

## 7. Si algo falla

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| El lanzador dice que el puerto está ocupado | Otra app usa el 8000 | `python scripts/run_demo.py --port 8010` y cambia `baseUrl` |
| Falla la instalación de dependencias | Python 3.14+ sin paquetes compilados | Instala Python 3.12 y ejecuta de nuevo |
| PowerShell no deja ejecutar `run-demo.ps1` | Política de ejecución | `powershell -ExecutionPolicy Bypass -File .\run-demo.ps1` |
| Token válido pero recibes 403 | Secreto distinto entre servidor y generador, o token expirado | Regenera el token con `generate_token.py`; en AWS verifica que `JwtSecret` sea igual al `.env` |
| AWS tarda mucho la primera vez | Cold start | Haz una petición de calentamiento antes de exponer |
| AWS responde 5xx | Error en la Lambda | `sam logs --stack-name rfha-demo --region us-east-1` |
| `sam deploy` da `AccessDenied` | Faltan permisos del usuario IAM | Revisar que `rfha-deployer` tenga las 6 políticas del paso 3 (sección 3.2) |
| Thunder Client no muestra la colección | La extensión no leyó `thunder-tests/` | Usa los `curl` de la sección 4 |
| Sin internet el día de la clase | | Usa solo el Plan A (local) |

---

## 8. Por qué cumple con la exposición y con la propuesta

### 8.1 Cumple con la exposición de Middleware y Web Services

La exposición pide mostrar un middleware y un web service funcionando. La demo lo hace así:

| Lo que se espera | Cómo lo cumple la demo | Dónde se ve |
|---|---|---|
| **Middleware**: software intermedio que independiza las aplicaciones del hardware, del sistema operativo y de los protocolos, y da visión de sistema único | El cliente solo conoce una URL. No sabe en qué servidor, sistema operativo o base de datos está el dato. Funciona igual en local y en AWS sin cambiar el cliente. | `demo/main.py`, endpoint único; Thunder Client con entornos `Local` y `AWS` |
| **Función de transportista**: recibe la petición y la encamina al destino | API Gateway recibe la petición HTTP y la entrega a la Lambda; FastAPI decide la ruta. | `demo/template.yaml` (`HttpApi` + `Function`), `Mangum` |
| **Servicio de seguridad** en la capa intermedia | El middleware valida el token de consentimiento antes de tocar los datos. | `verify_student_token()` |
| **Ocultar la heterogeneidad** de los datos | El cliente recibe siempre JSON estándar. Hoy el dato viene de un diccionario simulado; mañana vendrá de DynamoDB de cada universidad y el cliente no cambia. | `MOCK_DYNAMODB_NODES` |
| **Web Service**: comunicación entre aplicaciones con estándares abiertos | API **REST** sobre **HTTP**, método `GET`, datos en **JSON**, códigos de estado estándar (200, 403, 404). | Endpoint `GET /api/v1/federated/academic-history/{student_id}` |
| **Contrato documentado** | FastAPI genera la especificación OpenAPI/Swagger sola. | `/docs` |
| **Interoperabilidad** | Cualquier cliente que hable HTTP (Thunder Client, curl, navegador, otra universidad) usa el servicio igual. | Pruebas con `curl` y Thunder Client |

Transparencias de Sistemas Distribuidos que se pueden demostrar en vivo:
- **De acceso:** una sola interfaz REST sin importar cómo se guarde el dato.
- **De ubicación:** el cliente no conoce la IP, la región ni la base de datos. Se nota al cambiar de `Local` a `AWS`: cambia la URL y todo lo demás sigue igual.
- **De escalado (se explica, no se mide):** en AWS, Lambda crea instancias según la demanda sin cambiar el código.

### 8.2 Cumple con la propuesta del proyecto (RFHA-IES)

La demo es un recorte funcional de la propuesta. Implementa la parte central: **consultar un historial solo con el consentimiento del estudiante**.

| Requisito de la propuesta | Estado en la demo |
|---|---|
| **HU-06** Consulta federada: el funcionario consulta con el token del estudiante y recibe el historial | **Cumplido en su versión mínima.** `GET` con `X-Student-Consent-Token` devuelve el historial en JSON. |
| **HU-07** Bloqueo de consultas no autorizadas: sin token o expirado, `403` sin consultar los datos | **Cumplido.** Sin token, token inválido, expirado o de otro estudiante dan `403` antes de buscar el dato. |
| **RF-05** Consulta transparente por el middleware | **Cumplido (mínimo).** Una sola URL; el dato se obtiene detrás del middleware. |
| **RF-06** Rechazo por ausencia o expiración del token con `HTTP 403` | **Cumplido.** Probado con tres casos en `demo/tests`. |
| **RF-07** Visualización del historial (materias, créditos, calificaciones) | **Parcial.** Devuelve materias, calificaciones y promedio. Faltan los créditos por materia y la pantalla (llega en el frontend). |
| **Token de consentimiento JWT firmado** (`student_auth_token`) | **Cumplido.** JWT firmado con HS256 y fecha de expiración obligatoria. |
| **Arquitectura Serverless en AWS Free Tier** (API Gateway + Lambda, Python 3.11, FastAPI + Mangum) | **Cumplido.** Es exactamente el stack propuesto; la plantilla `demo/template.yaml` lo despliega. |
| **HTTPS** | **Cumplido en AWS.** API Gateway entrega HTTPS por defecto. En local es HTTP porque es solo desarrollo. |
| **Costo cero** | **Cumplido.** Solo Lambda y API Gateway, sin DynamoDB; logs a 7 días y límite de peticiones por segundo. |
| **Escenarios de la sección K** (sin token → 403; con token → 200) | **Cumplido y ampliado**, con corrección: el documento original devolvía 422 en vez de 403 al faltar el header. |

#### Lo que la demo todavía no cubre (se construye con HU-01 a HU-09)
Para no sobreprometer en la exposición, esto es lo que **no** hace la demo:
- Registro y aprobación de nodos universitarios y API Keys (HU-01 y HU-02). HU-01 ya está en `dev`.
- Carga de historiales y datos en DynamoDB por universidad (HU-03). Los datos son simulados.
- Generación y revocación del token por el estudiante (HU-04 y HU-05). Los tokens los genera un script.
- Enrutamiento real entre varias universidades con catálogo de nodos (HU-06 completa).
- Failover a réplica y `X-Data-Source` (HU-08).
- Bitácora de auditoría (HU-09).
- Que el token sirva solo para la universidad destino autorizada (HU-07 completa).

#### Cómo decirlo en la exposición
> "La demo implementa el corazón de la propuesta: el middleware que solo entrega el historial académico cuando el estudiante dio su consentimiento firmado. Usa el mismo stack del proyecto final, API Gateway, Lambda y FastAPI, y ya corre en AWS. Los demás módulos, como registro de universidades, DynamoDB por nodo, failover y auditoría, se construyen sobre esta base."
