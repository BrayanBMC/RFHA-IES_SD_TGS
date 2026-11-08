# Registro de decisiones

Cada decisión toma la opción más simple. Si no estás de acuerdo con alguna, dilo y se cambia.

| ID | Decisión | Motivo | Alcance |
|---|---|---|---|
| D-01 | Python 3.11 como versión objetivo (`.python-version`). Se acepta 3.12 en local. | Igual que el runtime de Lambda. Python 3.15 local puede no tener wheels. | Global |
| D-02 | Una sola Lambda con FastAPI + Mangum. | Menos piezas; cumple la transparencia igualmente. | App final y demo |
| D-03 | Cliente de pruebas: Thunder Client, colecciones en `thunder-tests/` dentro del repo. | Portabilidad entre PCs. | Global |
| D-04 | `demo/` y `src/app/` no se importan entre sí. Puertos 8000 (demo) y 8001 (app). | Evitar acoplamiento. | Global |
| D-05 | Header de nodo: `X-Node-API-Key`. Header de réplica: `X-Data-Source` con `Primary` o `Replica`. | Resolver inconsistencias A1 y A2. | App final |
| D-06 | Variables de entorno en `.env` (ignorado) y `.env.example` (versionado). `JWT_SECRET` tiene un valor por defecto solo para desarrollo local. | Sin secretos en git. | Global |
| D-07 | Despliegue con AWS SAM. La demo en el stack `rfha-demo`, independiente del de la app final. | Aislar demo y app. | AWS |
| D-08 | Cifrado en reposo: el predeterminado de DynamoDB (clave propiedad de AWS), sin KMS propio. | KMS propio cuesta. | AWS |
| D-09 | Logs de CloudWatch con retención de 7 días. | Evitar costos ocultos. | AWS |
| D-10 | Concurrencia reservada de Lambda: no se fija por defecto. | Cuentas nuevas pueden no permitirla (BRECHAS C2). | AWS |
| D-11 | Dependencias con versiones fijadas en `requirements.txt`. | Mismo entorno en todos los PCs. | Global |
| D-12 | Ramas: `feature/hu-xx-nombre`; demo en su propia rama `feature/demo-middleware` y tag `demo-martes`; correcciones en `fix/demo-...`. | Flujo del prompt. | Git |
| D-13 | (Reemplazada por el usuario) Se hace commit y push a la rama `dev` al terminar cada historia. GitHub Actions corre las pruebas (CI). Con las pruebas en verde y probado por el usuario, el usuario escribe "aprobado" y se avanza a la siguiente historia. | El "aprobado" ya no bloquea el commit, bloquea el avance. | Git |
| D-14 | CD: workflow manual (`workflow_dispatch`) que despliega con SAM solo si existen los secretos de AWS en GitHub. Nunca automático en cada push. | Evitar costos y despliegues accidentales. | GitHub / AWS |
| D-16 | Frontend de la demo: HTML/CSS/JS nativos servidos por la misma API (`demo/static`), sin framework ni build. Modo demostración (`DEMO_MODE=1`) habilita botones que simulan el consentimiento; apagado por defecto y en AWS. | Lo más simple, idéntico en local y AWS, sin dependencias. | Demo |
| D-17 | Frontend de la app final: se construye después de la HU-09 reutilizando el mismo sistema de diseño (`demo/static/styles.css`) copiado a `src/app/static/`. Mientras tanto, Thunder Client. Avísame si prefieres hacerlo por historia. | Evita rehacer pantallas mientras las APIs cambian. | App final |
| D-15 | La demo valida que el claim `student_id` del token coincida con el `student_id` de la URL. | Un token de un estudiante no debe abrir el historial de otro. | Demo |
| D-18 | Se agrega HU-10 (interfaz web de la app final) después de HU-09, con los requerimientos RF-11 a RF-19 y RNF-F1 a RNF-F9 en `docs/ADENDA_FRONTEND.md`. El prompt (`docs/PROMPT-AGENTE-RFHA-IES.md`, v2) incorpora la sección 10 de frontend. | El alcance incluía una aplicación web sin historia de usuario. | Planeación |
| D-19 | La interfaz se sirve desde la misma Lambda; no se crean S3 ni CloudFront. | Cero costo y cero recursos nuevos. | AWS |
| D-20 | El documento original `levantamiento_de_requerimientos_proyecto_final.md` no estaba en el repo. Se mantiene fuera y la adenda lo complementa. | Evitar duplicar el documento. | Planeación |
| D-21 | Todo desarrollo se registra en `docs/BITACORA.md` antes de cada commit; la regla quedó en el prompt (regla 11 y paso 7 del flujo). | Trazabilidad para el equipo y los docentes. | Proceso |
| D-22 | Los datos de la demo son 6 estudiantes ficticios en 4 universidades (`demo/students.py`). El selector de estudiantes de ejemplo y el endpoint `/api/v1/demo/students` solo existen en modo demostración. | Cubrir los casos de una exposición de 10 a 14 minutos sin exponer un listado de estudiantes en AWS. | Demo |
| D-23 | HU-01 incluye el formulario web `/registro-nodo` (RF-13) además de la API; el resto de pantallas sigue en HU-10. | El criterio de aceptación de HU-01 habla de un formulario. | App final |
