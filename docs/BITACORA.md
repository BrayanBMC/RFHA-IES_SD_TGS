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

### 2026-11-09 · HU-02 a HU-05, despliegue en AWS y guías de la demo y de la app final
- **Qué se hizo:**
  - **HU-02:** aprobación de nodos (`GET /api/v1/admin/nodes`, `POST /api/v1/admin/nodes/{id}/approve`) con `X-Admin-Key`; la API Key se muestra una sola vez y solo se guarda su SHA-256; `GET /api/v1/nodes/active` público (código y nombre); pantalla `/admin`.
  - **HU-03:** `POST /api/v1/node/sync-records` con `X-Node-API-Key` (hasta 100 estudiantes, upsert, estado de asignaturas, firma SHA-256, clave del estudiante con PBKDF2); tabla `RecordsTable`; pantalla `/panel-nodo` con ejemplo de JSON.
  - **HU-04:** `POST /api/v1/student/auth-token` (JWT HS256 de 24 h con `sub`, `doc`, `origin`, `aud`, `jti`, `iat`, `exp`); `src/app/tokens.py` con `issue_token` y `verify_token`; tabla `TokensTable` con TTL; pantalla `/portal-estudiante`.
  - **HU-05:** `POST /api/v1/student/tokens/list` y `.../{jti}/revoke`; lista negra como campo `revoked`; `verify_token` rechaza tokens revocados.
  - **Pruebas:** 112 en la app final y 39 en la demo: 151 en total, todas en verde en local. Incluyen DynamoDB con `moto` y un flujo completo registro → aprobación → carga → token → revocación.
  - **AWS:** `template.yaml` pasa a 3 tablas, parámetros `JwtSecret` y `AdminKey` (`NoEcho`), Lambda de 1024 MB y 29 s; `deploy_aws.py` pasa esos secretos desde `.env`; se redesplegó `rfha-app` (misma dirección) y `smoke_aws.py app` recorre ahora HU-01 a HU-05 contra AWS: las 18 comprobaciones dieron `[OK]` (la primera corrida falló en un paso por un error del propio script de prueba, que en la petición de «clave incorrecta» no enviaba `target_node_id` y recibió 422 en vez de 401; se corrigió y se repitió completa). Se agregó `scripts/clean_aws_data.py` para vaciar las tablas.
  - **Documentación:** `docs/APP_FINAL.md` (nueva: cómo se conecta todo, cómo se comunica el código con AWS, tablas, seguridad y 14 escenas de prueba), `docs/DEMO.md` sección 4.11 (direcciones y comunicación código ↔ AWS) con las tablas de 4.10 actualizadas, `README.md` con direcciones, estado, contrato de la API y estructura, `docs/historias/HU-02.md` a `HU-05.md`, D-28 a D-32, `.env.example`.
  - **Lanzador local:** `run_demo.py` completa `.env` con `ADMIN_KEY` y la muestra al arrancar la app final.
- **Por qué:** petición del usuario: dejar HU-01 cerrada, avanzar hasta HU-05 de corrido, publicar las direcciones en el README y en la documentación, y explicar cómo se comunica el código con AWS en la demo y en la app final.
- **Archivos principales:** `src/app/{config,models,repositories,security,tokens,main}.py`, `src/app/routers/{admin,sync,students,nodes}.py`, `src/app/static/{admin,panel-nodo,portal-estudiante}.{html,js}`, `common.js`, `styles.css`, `template.yaml`, `scripts/{deploy_aws,smoke_aws,clean_aws_data,run_demo}.py`, `tests/`.
- **Commit / CI:** ver el último commit de `dev` · el resultado del CI se verifica en GitHub Actions.
- **Decisiones:** D-28 a D-32.
- **Incidencias:** la terminal del entorno tuvo una cola de comandos atrasados; sus `git add -A; git commit; git push` (pensados para el cierre de AWS) se ejecutaron más tarde, a mitad de esta tarea, y dejaron en `dev` dos commits intermedios con el mensaje «feat(aws): …» que contienen trabajo parcial de HU-02 a HU-05. No se reescribió el historial (sin `push --force`); el commit final los completa.
- **Pendiente / riesgos:** la app final no tiene límite de intentos por cédula (solo el límite de tasa de API Gateway); HU-01 a HU-05 sin revisión manual con lector de pantalla; `smoke_aws.py` deja una universidad «Universidad de Prueba Humo» en las tablas (limpiar con `clean_aws_data.py`); la demo sigue con `DemoMode=1` (borrar o redesplegar con 0 después de la exposición); `README.md` y guías muestran la dirección pública de AWS.

### 2026-11-08 · Conexión a AWS, preparación del despliegue de la demo y la app final, y qué hace AWS en cada escena
- **Qué se hizo:**
  - **Conexión:** se instaló `uv` y AWS CLI 2.39.6, se inició sesión con el perfil `rfha` (región `us-east-2`, proyecto `329756216968`, plan **Free** activo con USD 100 de créditos hasta 2027-05-09) y se ejecutó `aws configure agent-toolkit` (25 habilidades instaladas y servidor MCP `aws-mcp` configurado). Las reglas del Agent Toolkit quedaron en `.kiro/steering/aws-agent-toolkit-rules.md`.
  - **Región:** el proyecto está en `us-east-2` (Ohio); se cambió `us-east-1` por `us-east-2` en `docs/DEMO.md`, `docs/AWS_PASO_A_PASO.md` y `.github/workflows/cd-demo.yml`.
  - **Python 3.12:** las Lambdas pasan a `python3.12` (`demo/template.yaml`, `template.yaml`); la guía de AWS y `cd-demo.yml` usan Python 3.12.
  - **App final en AWS:** nueva plantilla `template.yaml` (Lambda `rfha-app`, HTTP API, tabla DynamoDB de nodos en modo bajo demanda, rol mínimo sobre esa tabla, registros a 7 días), `scripts/prepare_app_package.py` (arma `build/app` con `src/`) y `src/requirements-lambda.txt`. `build/` se ignora en Git.
  - **Documentación:** nueva sección 6.5 de `docs/DEMO.md`: herramientas usadas (AWS CLI, Agent Toolkit, SAM CLI, CloudFormation, S3, IAM, API Gateway, Lambda, CloudWatch, variables de entorno, DynamoDB), el recorrido de cada consulta en AWS, una tabla de **qué hace AWS y qué decide el middleware en las 15 escenas**, dónde verlo en la consola y qué ocurre al registrar una universidad en la app final.
- **Estado del despliegue:** **hecho.** La instalación de SAM CLI se descartó (compilaba `pydantic-core` desde código fuente y bloqueó la terminal). Se reemplazó por `scripts/deploy_aws.py`, que solo usa el AWS CLI y Python 3.12: arma el paquete con librerías para Lambda/Linux, crea el depósito S3 `rfha-deploy-<cuenta>-us-east-2`, ejecuta `aws cloudformation package` y `deploy`. Se desplegaron `rfha-demo` (con `DemoMode=1`) y `rfha-app` (con su tabla DynamoDB) en `us-east-2`. `scripts/smoke_aws.py` comprobó contra las URLs reales: demo 9/9 y app final 4/4 correctas (arranque en frío de 2 a 7 s; después unos 0,3 s). Las URLs no se publican en el repositorio.
- **Archivos:** `template.yaml`, `demo/template.yaml`, `scripts/prepare_app_package.py`, `src/requirements-lambda.txt`, `.gitignore`, `.github/workflows/cd-demo.yml`, `docs/DEMO.md`, `docs/AWS_PASO_A_PASO.md`, `.kiro/steering/aws-agent-toolkit-rules.md`, `docs/BITACORA.md`.
- **Pendiente / riesgos:** la demo quedó con `DemoMode=1` (cualquiera con la URL puede generar tokens): borrarla tras la exposición con `scripts/deploy_aws.py demo --delete` o redesplegar con `--demo-mode 0`. La guía (pasos 7 a 9 y 14) se reescribió para el script, pero esa guía para otra persona no se ha seguido de principio a fin en otro computador. El flujo `cd-demo.yml` usa ahora el mismo script y no se ha ejecutado. Consumo de créditos: no se ha revisado en `Bills`.

### 2026-11-08 · Guía de AWS detallada, redacción neutra y corrección de la ruta raíz
- **Qué se hizo:**
  - **Redacción neutra:** en `docs/DEMO.md`, el README, `AWS_PASO_A_PASO.md`, `BRECHAS.md` y el prompt se reemplazaron las menciones a una persona concreta («el compañero de AWS», «Brayan lo genera») por «quien despliega en AWS» y «quien conoce el proyecto», para evitar malentendidos en el equipo.
  - **Sección 4 de `DEMO.md` reescrita a fondo:** mapa de fases; 14 pasos con el menú exacto de la consola de AWS donde entrar, qué botón pulsar y qué debe verse (cuenta y plan Free, alerta de USD 0.01, usuario IAM con las 6 políticas y llaves de acceso, instalación de herramientas, `aws configure`, descarga del código, secreto, `sam build`, `sam deploy` con cada parte del comando explicada, apertura de la demo, recorrido por CloudFormation, Lambda, API Gateway y CloudWatch, revisión de costos y borrado completo incluyendo S3 e IAM); despliegue alternativo desde GitHub paso a paso; tabla de problemas frecuentes.
  - **Qué código modificar y dónde (paso 6.2):** `demo/template.yaml` mostrado completo y comentado, con 5 cambios posibles (A versión de Python, B nombre en uso, C botones encendidos por defecto, D límite de peticiones, E tiempo máximo) indicando la línea a buscar y cómo debe quedar.
  - **Corrección de un error real:** la API de AWS solo enrutaba `/{proxy+}`, que **no cubre la ruta raíz `/`**; al abrir la URL pública habría salido `{"message":"Not Found"}` en vez de la pantalla. Se agregó el evento `Root` (`Path: /`) en `demo/template.yaml`.
  - **Flujo de GitHub:** `cd-demo.yml` ahora permite elegir el modo demostración (0 o 1) y muestra la URL de la demo al terminar.
- **Por qué:** petición del usuario: guía de AWS muy detallada con menús y código a modificar, y redacción general sin señalar a nadie.
- **Archivos:** `docs/DEMO.md`, `demo/template.yaml`, `.github/workflows/cd-demo.yml`, `README.md`, `docs/AWS_PASO_A_PASO.md`, `docs/BRECHAS.md`, `docs/PROMPT-AGENTE-RFHA-IES.md`, `docs/BITACORA.md`.
- **Pendiente / riesgos:** **no se ha desplegado en una cuenta real**. Los nombres de menús de la consola de AWS se escribieron de memoria y AWS cambia su diseño con frecuencia; la guía lo advierte y da la barra de búsqueda como respaldo. La corrección de la ruta raíz no se ha probado en AWS (en local no aplica). Verificar con el primer despliegue.

### 2026-11-08 · DEMO.md sin guion; el middleware explicado en cada escena
- **Qué se hizo:** se eliminó de `docs/DEMO.md` la sección «Guion de la exposición» (tabla minuto a minuto) y los «Qué decir» de cada escena; en su lugar la sección 7 es una lista de verificación previa a exponer. En las pruebas se agregó la sección 6.2 «Cómo viaja una consulta» (recorrido navegador, API Gateway, Lambda, controles y respuesta, con una tabla de qué revisa cada uno de los 4 controles y qué responde si falla) y **cada una de las 15 escenas** ahora tiene «Cómo se refleja el middleware» (petición, qué control pasa o falla, decisión y respuesta) y «Conclusión». Se explicó para qué sirve «Copiar como curl» (escena 14) y la tabla resumen (6.4) incluye cómo lo resuelve el middleware en cada caso.
- **Por qué:** petición del usuario: el documento debe mostrar cómo funciona y cómo se refleja el middleware en cada prueba, no un guion.
- **Archivos:** `docs/DEMO.md`, `README.md`, `docs/BITACORA.md`.
- **Pendiente / riesgos:** las explicaciones se basan en el código (`demo/main.py`); confirmar los textos de cada escena en pantalla. `docs/DEMO_MARTES.md` conserva su propio guion breve; decidir si también se retira.

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
- **Qué se hizo:** la sección 3 de `docs/DEMO.md` se reescribió para que quien despliegue en AWS pueda hacerlo sin abrir otro documento: resumen (qué se crea, costo, tiempo, quién hace qué), 12 pasos con comandos exactos de PowerShell (cuenta con plan Free, alerta de USD 0.01, usuario IAM con 6 políticas, instalación de AWS CLI, SAM CLI, Python 3.11 y Git, `aws configure`, clonar, secreto JWT, `sam build`, `sam deploy`, comprobar URL, prueba completa con `check_demo.py`, entrega a Brayan), despliegue alternativo desde GitHub Actions, logs, actualización y borrado. Se quitaron las referencias a otros `.md`.
- **Por qué:** petición del usuario: quien despliegue debe poder levantar la demo en AWS solo con ese documento.
- **Archivos:** `docs/DEMO.md`, `docs/BITACORA.md`.
- **Pendiente / riesgos:** los comandos no se han ejecutado contra una cuenta AWS real. Riesgo conocido: `sam build` exige Python 3.11 local (se instala en el paso 4). Probar el despliegue completo con el equipo y corregir la guía si algo difiere.

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
- **Pendiente:** el usuario debe escribir «aprobado» para pasar a HU-02. Falta crear `NodesTable` en AWS.

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
- **AWS:** nada desplegado aún. Pendiente en AWS: cuenta con plan Free, presupuesto de USD 0.01, usuario IAM, CLI y SAM, despliegue de la demo (bloque 1 de `docs/AWS_PASO_A_PASO.md`) y tabla `NodesTable`.
