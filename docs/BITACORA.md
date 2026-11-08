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

### 2026-11-08 · Declaración de uso de IA en la documentación
- **Qué se hizo:** se agregó al `README.md` la sección 16 «Declaración de uso de herramientas de IA» (herramienta, para qué se usó, cómo se trabajó, qué decide el equipo, trazabilidad y responsabilidad). Se verificó con una búsqueda que ni el frontend (`demo/static`, `src/app/static`) ni el código de la API contienen menciones a herramientas de IA.
- **Por qué:** la asignatura permite el uso de IA declarado; la declaración va en la documentación y no en la interfaz.
- **Archivos:** `README.md`, `docs/BITACORA.md`.
- **Decisiones:** D-24 (la declaración de IA vive solo en la documentación).

### 2026-11-08 · Texto de ayuda del token retirado de la pantalla de la demo
- **Qué se hizo:** se quitó el texto de ayuda bajo el campo del token («Se envía en el encabezado X-Student-Consent-Token. Déjalo vacío para probar el rechazo.»), porque es una indicación para quien presenta y no para el público. El campo conserva su etiqueta y un texto de ejemplo más corto.
- **Archivos:** `demo/static/index.html`.

### 2026-11-08 · README completo
- **Qué se hizo:** el `README.md` se reescribió con: ficha del proyecto, resumen y problema, alcance y actores, requerimientos funcionales (RF-01 a RF-19) y no funcionales con su estado, tabla de historias de usuario HU-01 a HU-10 con estado, arquitectura (diagrama Mermaid), stack, modelo de datos, mapeo con las 8 transparencias de Sistemas Distribuidos y con Teoría General de Sistemas, resumen de lo hecho, cronograma, riesgos y flujo de Git. La sección «Cómo ejecutarlo desde la terminal de VS Code» explica paso a paso cómo abrir la terminal y lanzar la demo y la app final, con comandos para **Windows y para macOS/Linux** (se mantienen ambos a pedido del usuario), problemas frecuentes y cómo correr las pruebas.
- **Por qué:** el README debía reflejar el levantamiento de requerimientos, las historias de usuario y el avance real, y explicar la ejecución desde VS Code.
- **Archivos:** `README.md`, `run-demo.sh` (se conserva), `docs/DEMO.md`, `docs/historias/HU-01.md`, `docs/PROMPT-AGENTE-RFHA-IES.md`, `docs/BITACORA.md`.
- **Nota:** durante la sesión se quitaron y se restauraron los comandos de macOS/Linux por un cambio de instrucción; el estado final los conserva.
- **Pendiente:** los autores aparecen solo con nombre (sin códigos estudiantiles) porque el repositorio es público.

### 2026-11-08 · Reescritura de la guía de la demo (DEMO.md) más clara y centrada en la pantalla
- **Qué se hizo:** `docs/DEMO.md` se reescribió completo: resumen de 2 minutos; glosario que explica cada concepto con su ejemplo en la demo (IES, homologación, créditos, token, JWT, firma, middleware, API REST, JSON, códigos 200/403/404, serverless, Lambda, API Gateway, cold start, localhost, etc.); mapa de la pantalla con cada campo y botón; **15 escenas de prueba hechas solo con clics** (qué pulsar, qué se ve, qué decir) más una tabla resumen de rechazos; guion de 12 a 14 minutos que enlaza las escenas; tabla de fallos en vivo con salida por clics; y los comandos relegados a un apéndice de respaldo.
- **Decisión de despliegue en AWS:** para poder hacer las pruebas con clics también en AWS, la guía recomienda desplegar con `DemoMode=1` para la exposición y borrar el paquete (`sam delete`) al terminar, explicando el riesgo (con `1`, quien conozca la URL puede generar tokens). Con `DemoMode=0` quedan los botones apagados.
- **Por qué:** petición del usuario: más fácil de comprender, todos los conceptos explicados y pruebas hechas en el frontend delante del público.
- **Archivos:** `docs/DEMO.md`, `docs/AWS_PASO_A_PASO.md`, `docs/DEMO_MARTES.md`, `docs/BITACORA.md`.
- **Pendiente / riesgos:** las cifras de homologación y los mensajes que se citan en las escenas salen del código y de cálculos a mano; confirmar en pantalla. La guía de AWS sigue sin probarse contra una cuenta real.

### 2026-11-08 · Datos de prueba ampliados, guion de 12 a 14 minutos y HU-01 completa
- **Qué se hizo:**
  - **Datos de la demo:** de 1 a 6 estudiantes ficticios en 4 universidades (`demo/students.py`), con estados académicos (activo, graduado, retirado), créditos, asignaturas por semestre, materias reprobadas y repetidas, y asignaturas en curso.
  - **Interfaz de la demo:** selector «Estudiante de ejemplo» (solo modo demostración, endpoint `GET /api/v1/demo/students`), estado académico, barra de créditos, título y fecha de grado, tabla con créditos, nota y estado, y panel «Apoyo a la homologación» con nota mínima ajustable.
  - **Guion:** `docs/DEMO.md` ahora trae la tabla de datos de prueba, los casos 11 a 16 y un guion minuto a minuto de 12 a 14 minutos (10 minutos recortando los bloques opcionales), con preguntas probables de los docentes.
  - **HU-01 terminada:** formulario web `/registro-nodo` en la app final (HTML accesible, validación en pantalla con las mismas reglas del servidor, errores por campo, confirmación con el código del nodo), CSP estricta, lanzador `run-app.cmd` / `--app` (puerto 8001) y job de CI que levanta la app final. `docs/historias/HU-01.md` reescrita con todos los cambios, 12 casos de prueba del formulario y la matriz de criterios.
- **Por qué:** la demo debía durar al menos 10 minutos y tener más de un dato; HU-01 pedía un formulario y solo existía la API.
- **Archivos:** `demo/students.py`, `demo/main.py`, `demo/static/*`, `demo/tests/test_demo_data.py`, `demo/tests/test_demo_api.py`, `src/app/main.py`, `src/app/static/*`, `tests/test_hu01_frontend.py`, `scripts/run_demo.py`, `run-demo.ps1`, `run-app.cmd`, `.github/workflows/ci.yml`, `thunder-tests/thunderclient.json`, `docs/DEMO.md`, `docs/historias/HU-01.md`, `README.md`.
- **Decisiones:** D-22 (datos ficticios y selector solo en modo demostración), D-23 (HU-01 incluye el formulario web).
- **Pendiente / riesgos:** no se ha visto la interfaz en un navegador desde el agente; validar a mano. Las cifras de los casos 11 a 15 se calcularon a mano contra los datos; si alguna no coincide en pantalla, corregir la guía. Revisión con lector de pantalla pendiente.

### 2026-11-08 · Guía de AWS autosuficiente en DEMO.md
- **Qué se hizo:** la sección 3 de `docs/DEMO.md` se reescribió para que el compañero de AWS despliegue la demo sin abrir otro documento: resumen (qué se crea, costo, tiempo, quién hace qué), 12 pasos con comandos exactos de PowerShell (cuenta con plan Free, alerta de USD 0.01, usuario IAM con 6 políticas, instalación de AWS CLI, SAM CLI, Python 3.11 y Git, `aws configure`, clonar, secreto JWT, `sam build`, `sam deploy`, comprobar URL, prueba completa con `check_demo.py`, entrega a Brayan), despliegue alternativo desde GitHub Actions, logs, actualización y borrado. Se quitaron las referencias a otros `.md`.
- **Por qué:** petición del usuario: el compañero debe poder levantar la demo en AWS solo con ese documento.
- **Archivos:** `docs/DEMO.md`, `docs/BITACORA.md`.
- **Pendiente / riesgos:** los comandos no se han ejecutado contra una cuenta AWS real. Riesgo conocido: `sam build` exige Python 3.11 local (se instala en el paso 4). Probar el despliegue completo con el compañero y corregir la guía si algo difiere.

### 2026-11-08 · Guía de casos de prueba y bitácora
- **Commit / CI:** `ca500d3` · verde.
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
- **Historias:** HU-01 terminada, con API y formulario web (espera «aprobado»). HU-02 a HU-10 pendientes.
- **Pruebas definidas en el código:** 61 = demo (9 de la API, 22 de los datos, 8 de la interfaz) + app final (12 de HU-01 API y 10 del formulario). Se ejecutan en GitHub Actions, más el job `demo-runner` (levanta la demo y la app final).
- **AWS:** nada desplegado aún. Pendiente del compañero: cuenta con plan Free, presupuesto de USD 0.01, usuario IAM, CLI y SAM, despliegue de la demo (bloque 1 de `docs/AWS_PASO_A_PASO.md`) y tabla `NodesTable`.
