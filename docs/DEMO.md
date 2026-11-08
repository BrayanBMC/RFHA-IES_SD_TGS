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
3. Instala dependencias: `pip install -r demo/requirements.txt`
4. Crea el secreto. Crea un archivo `.env` en la raíz con una línea:
   ```
   JWT_SECRET=pon-aqui-un-texto-aleatorio-de-mas-de-32-caracteres
   ```
   (o copia `.env.example` a `.env`). Si no creas `.env`, la demo usa un secreto de desarrollo inseguro; sirve en local, nunca en AWS.
5. Genera los tokens: `python scripts/generate_token.py`. Copia el **válido** y el **expirado**.
6. Levanta la API: `uvicorn demo.main:app --port 8000`
7. En otra terminal, verifica: `python scripts/check_demo.py http://127.0.0.1:8000` → debe decir `TODO BIEN`.

### 2.3 Probar en local con Thunder Client

1. Abre la extensión **Thunder Client** (icono del rayo).
2. Pestaña *Collections* → **RFHA-IES** → carpeta **Demo** (tres requests).
3. Pestaña *Env* → selecciona **Local**. Pega los tokens en `validToken` y `expiredToken`.
4. Ejecuta en orden: `1. Sin token (403)`, `3. Token expirado (403)`, `2. Token valido (200)`.

Si no aparece la colección, usa `curl` (sección 4).

### 2.4 Probar desde el navegador

Abre `http://127.0.0.1:8000/docs`. Es la documentación Swagger generada automáticamente. Pulsa *Try it out* en el endpoint, escribe el `student_id` `20262678029` y el token en el campo del header.

---

## 3. Levantar y probar en AWS

Esta parte la hace quien administra la cuenta AWS. Resultado: una URL pública `https://xxxx.execute-api.us-east-1.amazonaws.com` que responde igual que el local. Se crea el stack **`rfha-demo`** (una Lambda + un API Gateway + logs a 7 días). No usa DynamoDB.

> Costo: dentro del Free Tier. Usa una cuenta con plan **Free** y la alerta de USD 0.01 (detalle en `docs/AWS_PASO_A_PASO.md`, pasos 1.1 a 1.5). Si ya hiciste esos pasos, ve directo al 3.2.

### 3.1 Preparación (una sola vez)
1. Cuenta AWS con plan Free y presupuesto de USD 0.01 (`AWS_PASO_A_PASO.md`, 1.1 y 1.2).
2. Usuario IAM `rfha-deployer` con su Access Key (`AWS_PASO_A_PASO.md`, 1.3).
3. Instalar herramientas (PowerShell): `winget install Amazon.AWSCLI` y `winget install Amazon.SAM-CLI`. Cerrar y abrir la terminal.
4. `aws configure` → pegar Access Key, Secret, región `us-east-1`, formato `json`.
5. Comprobar: `aws sts get-caller-identity` muestra la cuenta.

### 3.2 Desplegar
En la raíz del proyecto:

1. **Secreto.** Debe ser el mismo que usarás para generar tokens. Si ya tienes `.env` local con `JWT_SECRET`, úsalo. Si no:
   ```
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
   Guárdalo en `.env` como `JWT_SECRET=...`. No lo subas a git ni lo pegues en chats públicos.
2. **Construir:**
   ```
   sam build --template-file demo/template.yaml
   ```
   Esperado: `Build Succeeded`.
3. **Desplegar** (reemplaza `<SECRETO>`):
   ```
   sam deploy --template-file .aws-sam/build/template.yaml --stack-name rfha-demo --resolve-s3 --capabilities CAPABILITY_IAM --region us-east-1 --parameter-overrides "JwtSecret=<SECRETO>"
   ```
   Si pregunta *Deploy this changeset?* responde `y`. Esperado: `Successfully created/updated stack - rfha-demo`.
4. **Copiar la URL.** Al final aparece en *Outputs*:
   ```
   Key    ApiUrl
   Value  https://abc123.execute-api.us-east-1.amazonaws.com
   ```
   Si se pierde: `aws cloudformation describe-stacks --stack-name rfha-demo --query "Stacks[0].Outputs"`.

Alternativa sin terminal local: en GitHub, *Actions → CD demo (manual) → Run workflow*. Requiere los secretos `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` y `DEMO_JWT_SECRET` en *Settings → Secrets and variables → Actions*.

### 3.3 Probar en AWS
1. **Calentamiento** (cold start): la primera petición tras un rato sin uso tarda 1 a 3 segundos. Haz una antes de exponer:
   ```
   curl -i https://abc123.execute-api.us-east-1.amazonaws.com/api/v1/federated/academic-history/20262678029
   ```
   Debe devolver `403`. Eso es correcto: confirma que la Lambda responde.
2. **Verificación automática** (con el mismo `JWT_SECRET` en tu `.env`):
   ```
   python scripts/check_demo.py https://abc123.execute-api.us-east-1.amazonaws.com
   ```
   Esperado: `TODO BIEN`.
3. **Thunder Client:** *Env* → **AWS** → cambia `baseUrl` por la URL de `ApiUrl` (sin barra final) y pega los tokens generados con `python scripts/generate_token.py`. Ejecuta las mismas 3 requests.

### 3.4 Ver logs si algo falla
```
sam logs --stack-name rfha-demo --region us-east-1
```

### 3.5 Borrar todo al terminar
```
sam delete --stack-name rfha-demo --region us-east-1
```

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
| `demo/main.py` | **Toda la API.** Validación del token, datos simulados y endpoint. |
| `demo/requirements.txt` | Librerías que necesita la Lambda en AWS. |
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
Automatiza lo que se haría a mano: crea `.venv`, instala dependencias si el hash de `demo/requirements.txt` cambió, crea `.env`, lanza `uvicorn` como subproceso, espera a que responda, ejecuta `check_demo.py`, imprime los tokens y se queda esperando hasta `Ctrl+C`, momento en que apaga el servidor.

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

Tiempo total: 7 minutos. Antes de empezar, revisa la lista de `docs/DEMO_MARTES.md`.

1. **Problema y rol del middleware (1.5 min).** Las universidades son islas de datos. El middleware es el transportista: una sola URL, sin IP ni motor de base de datos visibles.
2. **Sin token → 403 (1.5 min).** Ejecuta la request 1. *"El middleware corta antes de tocar los datos."*
3. **Token expirado → 403 (1 min).** Request 3. *"El consentimiento del estudiante es temporal."*
4. **Token válido → 200 (2 min).** Request 2. Muestra el JSON. *"Se validó la firma, se localizó el dato y se serializó en JSON."*
5. **Mismo código en AWS (0.5 min).** Cambia el entorno de Thunder Client a **AWS**; repite una request. *"Cambió la URL, no el código."*
6. **Cierre (0.5 min).** Transparencia de acceso y de ubicación.

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
| `sam deploy` da `AccessDenied` | Faltan permisos del usuario IAM | Revisar `AWS_PASO_A_PASO.md`, paso 1.3 |
| Thunder Client no muestra la colección | La extensión no leyó `thunder-tests/` | Usa los `curl` de la sección 4 |
| Sin internet el día de la clase | | Usa solo el Plan A (local) |
