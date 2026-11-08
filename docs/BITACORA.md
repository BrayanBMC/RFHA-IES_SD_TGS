# Bitácora de desarrollo — RFHA-IES

Registro cronológico de todo lo que se hace en el proyecto: qué, por qué, archivos, resultado del CI y pendientes. **Se actualiza en cada sesión de desarrollo, antes de hacer el commit.** Las más recientes van arriba.

## Cómo agregar una entrada

Copia esta plantilla al inicio de la sección «Entradas»:

```
### AAAA-MM-DD · Título corto
- **Qué se hizo:** …
- **Por qué:** …
- **Archivos:** …
- **Commit / CI:** `hash` · verde / rojo (error)
- **Decisiones:** (referencia a DECISIONES.md)
- **Pendiente / riesgos:** …
```

---

## Entradas

### 2026-11-08 · Guía de casos de prueba y bitácora
- **Qué se hizo:** se documentó en `docs/DEMO.md` qué escribir en cada campo de la interfaz y 10 casos de prueba (éxito, sin token, expirado, firma alterada, texto basura, token de otro estudiante, estudiante inexistente, código no válido, servidor apagado, JSON y curl), con la variante para AWS, Swagger y Thunder Client. Se creó esta bitácora y se agregó al prompt la regla de mantenerla.
- **Por qué:** el equipo necesita probar y exponer la demo sin adivinar valores; el prompt exige trazabilidad del desarrollo.
- **Archivos:** `docs/DEMO.md`, `docs/BITACORA.md`, `docs/PROMPT-AGENTE-RFHA-IES.md`, `docs/DECISIONES.md`, `README.md`.
- **Decisiones:** D-21 (bitácora obligatoria).

### 2026-11-08 · Documentación del frontend en planeación y prompt
- **Qué se hizo:** prompt v2 con sección de frontend y HU-10; adenda de requerimientos con RF-11 a RF-19, RNF-F1 a F9 y la historia HU-10; actualización de README, `DEMO_MARTES.md` y `AWS_PASO_A_PASO.md`.
- **Por qué:** el alcance original incluía una aplicación web sin historia de usuario (BRECHAS B10). El documento de requerimientos y el prompt no estaban en el repo.
- **Archivos:** `docs/PROMPT-AGENTE-RFHA-IES.md`, `docs/ADENDA_FRONTEND.md`, `docs/DECISIONES.md`, `README.md`, `docs/DEMO_MARTES.md`, `docs/AWS_PASO_A_PASO.md`.
- **Commit / CI:** `1aa409e` · verde (`test` y `demo-runner`).
- **Decisiones:** D-18, D-19, D-20.
- **Pendiente:** `.vscode/settings.json` entró en el commit modificado por un cambio ajeno; revisar el diff.

### 2026-11-08 · Interfaz web de la demo
- **Qué se hizo:** página única servida por la misma API (`demo/static/`): formulario, tarjeta de validación del middleware en 4 pasos, respuesta con insignia HTTP, expediente, JSON y «Copiar como curl». Modo demostración (`DEMO_MODE=1`) con botones que simulan al estudiante; apagado por defecto y en AWS (parámetro `DemoMode` en la plantilla SAM). Cabeceras de seguridad y CSP estricta. Endpoints `GET /api/v1/demo/config` y `POST /api/v1/demo/consent-token`.
- **Por qué:** petición de contar con un frontend agradable y moderno para exponer.
- **Archivos:** `demo/main.py`, `demo/static/*`, `demo/template.yaml`, `demo/tests/test_demo_frontend.py`, `scripts/run_demo.py`, `docs/DEMO.md`.
- **Commit / CI:** `6679bea` · verde.
- **Decisiones:** D-16 (HTML/CSS/JS nativos sin build), D-17 (frontend de la app final tras HU-09).
- **Pendiente:** no se ha revisado el aspecto visual en un navegador desde el agente; validar a mano.

### 2026-11-08 · Lanzador `.cmd` para Windows
- **Qué se hizo:** `run-demo.cmd`, que ejecuta `run-demo.ps1` saltando la política de ejecución de PowerShell.
- **Por qué:** el usuario recibió «la ejecución de scripts está deshabilitada en este sistema».
- **Archivos:** `run-demo.cmd`.
- **Commit / CI:** incluido en `6679bea`.

### 2026-11-08 · Corrección del lanzador y cumplimiento de la exposición
- **Qué se hizo:** corrección del lanzador (instalaba `demo/requirements.txt`, que no tiene `uvicorn`): nuevo `demo/requirements-local.txt`. Se agregó a `docs/DEMO.md` la sección 8 (por qué cumple la exposición de middleware y web services y la propuesta, y qué no cubre todavía).
- **Por qué:** el job `demo-runner` del CI se quedó colgado y reveló el error.
- **Archivos:** `demo/requirements-local.txt`, `scripts/run_demo.py`, `.github/workflows/ci.yml` (`timeout-minutes: 5`), `docs/DEMO.md`.
- **Commit / CI:** `a7d75ce` · verde (`test` y `demo-runner`).

### 2026-11-08 · Guía completa de la demo y lanzador de un comando
- **Qué se hizo:** `docs/DEMO.md` (local, AWS, explicación del código, guion, fallos comunes) y `scripts/run_demo.py` (crea `.venv`, instala, crea `.env`, levanta la API, verifica 3 escenarios, imprime tokens). Accesos: `run-demo.ps1`, `run-demo.sh`, tarea de VS Code. Job `demo-runner` en el CI.
- **Archivos:** `docs/DEMO.md`, `scripts/run_demo.py`, `run-demo.ps1`, `run-demo.sh`, `.vscode/tasks.json`, `.github/workflows/ci.yml`, `README.md`.
- **Commit / CI:** `4f33b36` · `test` verde; `demo-runner` falló por la falta de `uvicorn` (corregido en `a7d75ce`).

### 2026-11-08 · HU-01: registro de nodo IES
- **Qué se hizo:** `POST /api/v1/nodes/register` (201 con `node_id` y estado `PENDIENTE_APROBACION`, 409 si el NIT ya existe, 422 si los datos son inválidos). Repositorio con implementación en memoria y DynamoDB.
- **Archivos:** `src/app/{config,models,repositories,main}.py`, `src/app/routers/nodes.py`, `tests/test_hu01_register_node.py`, `docs/historias/HU-01.md`, `thunder-tests/`, `docs/AWS_PASO_A_PASO.md` (tabla `NodesTable`).
- **Commit / CI:** `8810c54` · verde.
- **Pendiente:** el usuario debe escribir «aprobado» para pasar a HU-02. El compañero de AWS debe crear `NodesTable`.

### 2026-11-08 · Demo del middleware (Prioridad 0)
- **Qué se hizo:** API de la demo con 403 (sin token, inválido, expirado, sin `exp`, token de otro estudiante), 200 y 404; plantilla SAM del stack `rfha-demo`; `scripts/generate_token.py` y `scripts/check_demo.py`; colección y entornos de Thunder Client; CI y CD manual. Etiqueta `demo-martes` sobre `1a1fd57`.
- **Por qué:** la demo es la exposición de la sección K y no debe frenar la app final.
- **Archivos:** `demo/*`, `scripts/*`, `thunder-tests/*`, `.github/workflows/{ci,cd-demo}.yml`, `docs/{DEMO_MARTES,AWS_PASO_A_PASO}.md`.
- **Commit / CI:** `1a1fd57` · verde. Pull request #2 de `dev` a `main`.
- **Decisiones:** D-14 (CD manual), D-15 (el token debe coincidir con el estudiante consultado).
- **Corrección al documento original:** el header opcional y el 403 manual (FastAPI responde 422 con un header requerido ausente); `exp` obligatorio.

### 2026-11-08 · Esqueleto portable y análisis de brechas
- **Qué se hizo:** `docs/BRECHAS.md` (inconsistencias, faltantes de diseño, Free Tier verificado, entorno), `docs/DECISIONES.md`, `.vscode/`, `.gitignore`, `.gitattributes`, `.python-version`, `requirements.txt` fijado, `.env.example`, `README.md`.
- **Hallazgos clave:** el Free Tier de cuentas nuevas desde el 15-jul-2025 es un plan de créditos de hasta 6 meses (no «para siempre» para API Gateway); la concurrencia reservada de 50 puede no ser posible en cuentas nuevas; KMS propio cuesta, se usa el cifrado por defecto de DynamoDB.
- **Commit / CI:** `7435210` en `main` (`.gitignore`, `.gitattributes`, `README.md`).
- **Decisiones:** D-01 a D-13.

---

## Incidencias y lecciones aprendidas

| Fecha | Incidencia | Causa | Solución / lección |
|---|---|---|---|
| 2026-11-08 | `pip install` y `pytest` no corrían en el PC | Python 3.15 local sin paquetes compilados | Instalar Python 3.12 con el Python install manager. Las pruebas oficiales corren en GitHub (Python 3.11). |
| 2026-11-08 | `demo-runner` del CI se quedó colgado | El lanzador instalaba `demo/requirements.txt` sin `uvicorn` | `demo/requirements-local.txt` y `timeout-minutes: 5` en el job. |
| 2026-11-08 | `run-demo.ps1` bloqueado en Windows | Política de ejecución de PowerShell | `run-demo.cmd`, que invoca PowerShell con `-ExecutionPolicy Bypass`. |
| 2026-11-08 | La terminal del agente devolvía vacío o con mucho retraso | Cola de comandos de la terminal integrada | Escribir la salida a un archivo en `%TEMP%` y leerla después; verificar el resultado en GitHub, no en la terminal. |
| 2026-11-08 | La API de GitHub devolvía estados viejos | Caché de respuestas | Repetir la consulta con un parámetro distinto (`per_page`). |

## Estado actual

- **Rama de trabajo:** `dev`. Etiqueta `demo-martes` en `1a1fd57`.
- **Historias:** HU-01 hecha (espera «aprobado»). HU-02 a HU-10 pendientes.
- **Pruebas definidas en el código:** 9 (API de la demo) + 8 (interfaz de la demo) + 12 (HU-01). Se ejecutan en GitHub Actions, más el job `demo-runner`.
- **AWS:** nada desplegado aún. Pendiente del compañero: cuenta con plan Free, presupuesto de USD 0.01, usuario IAM, CLI y SAM, despliegue de la demo (bloque 1 de `docs/AWS_PASO_A_PASO.md`) y tabla `NodesTable`.
