# Análisis de brechas RFHA-IES

Estados: `Abierta` · `Resuelta (propuesta)` · `Cerrada`.
Última revisión: Noviembre 2026 (antes de la Prioridad 0).

## A. Inconsistencias del documento

| # | Descripción | Impacto | Solución simple propuesta | Estado |
|---|---|---|---|---|
| A1 | La API Key del nodo va en `X-Node-API-Key` (HU-02/03) pero la sección K usa `Authorization: Bearer`. | El cliente no sabría qué header enviar. | Usar solo `X-Node-API-Key` para nodos. La demo no exige autenticación de IES (solo consentimiento). | Resuelta (propuesta) |
| A2 | Header de réplica: `X-Data-Source: Replica` (RF-09) vs `Backup-Replica` (HU-08). | Pruebas ambiguas. | Valores: `Primary` y `Replica`. | Resuelta (propuesta) |
| A3 | Tiempo objetivo 1.5 s (RF-05) vs 2000 ms (RNF y failover). | Criterio de aceptación incierto. | 1.5 s = meta de respuesta normal; 2000 ms = timeout para activar failover y tope RTT. | Resuelta (propuesta) |
| A4 | El código de la sección K usa `Header(...)` obligatorio: FastAPI devuelve 422, no 403. Además `exp` se valida dos veces y falla si falta `exp`. | La demo no cumpliría RF-06. | Header opcional, 403 manual; PyJWT valida `exp` con `options={"require": ["exp"]}`. | Resuelta (propuesta) |
| A5 | El `student_id` del ejemplo (`20262678029`) es código estudiantil, y `document_number` es la cédula. HU-06 dice "cédula". | Confusión sobre qué identifica al estudiante. | Ver B3. | Abierta |
| A6 | La arquitectura habla de "Lambda Auth" y "Lambda Router" separadas; el prompt pide una sola Lambda. | Diferencia con el diagrama. | Una sola Lambda con FastAPI + Mangum, con la validación como dependencia. | Resuelta (propuesta) |
| A7 | RF-05 pide retorno en < 1.5 s pero el cold start de Lambda puede superarlo. | Incumplimiento ocasional. | Documentar calentamiento antes de la demo; medir en HU-06. | Abierta |

## B. Faltantes de diseño

| # | Descripción | Impacto | Solución simple propuesta | Estado |
|---|---|---|---|---|
| B1 | Autenticación del estudiante (HU-04) no definida. | Sin ella no se puede emitir el token. | Cédula + clave sembrada por el nodo al sincronizar (hash con PBKDF2 de la stdlib). Sin Cognito. | Abierta (HU-04) |
| B2 | Autenticación de administrador general e institucional no definida. | HU-02 queda sin control de acceso. | Admin general: header `X-Admin-Key` desde variable de entorno. Admin institucional: su `X-Node-API-Key`. | Abierta (HU-02) |
| B3 | HU-06 consulta por cédula, pero la clave es `INSTITUCION#STUDENT_ID`. Falta saber en qué nodo está el estudiante. | El middleware no puede enrutar. | Tabla de enrutamiento `document_number -> institution_id, student_id`, poblada al sincronizar. Alternativa: el token ya trae `institution_id` de origen. | Abierta (HU-03/06) |
| B4 | Claims del JWT sin definir. | Sin `jti` no hay revocación. | `sub` (student_id), `doc` (cédula), `origin` (IES origen), `aud` (IES destino), `jti`, `iat`, `exp`. Validar `aud` contra la IES consultante. | Abierta (HU-04/07) |
| B5 | Lista negra de tokens. | Crece sin límite. | Tabla con clave `jti` y atributo `ttl` (TTL de DynamoDB = `exp` del token). | Abierta (HU-05) |
| B6 | `digital_signature_hash` sin definición. | No hay verificación de integridad. | SHA-256 del JSON canónico (claves ordenadas) del registro sin el campo de firma; se recalcula al leer. Para firma real, HMAC con clave del nodo. | Abierta (HU-03) |
| B7 | Réplica (HU-08) sin diseño. | No se puede probar el failover. | Segunda tabla en la misma región, escrita al sincronizar. Simular caída con variable `SIMULATE_NODE_DOWN=<institution_id>` que fuerza timeout. | Abierta (HU-08) |
| B8 | Inmutabilidad de bitácora (HU-09). | DynamoDB permite borrar/actualizar. | Rol IAM de la Lambda solo con `dynamodb:PutItem` sobre `AuditLogsTable`. | Abierta (HU-09) |
| B9 | "Notifica" en RF-02 y RF-04 sin servicio. | Requisito incumplible tal cual. | La respuesta de la API entrega la credencial una sola vez. SES queda opcional (fuera de alcance). | Abierta |
| B10 | Frontend (SPA) sin historia de usuario. | Alcance incluye interfaz pero no se planifica. | Thunder Client como interfaz durante las 9 HU. Después, HTML/JS estático opcional. Requiere decisión. | Abierta |
| B11 | CORS, validación de entradas y tope de tamaño en `sync-records`. | Riesgo de abuso. | Pydantic con límites; máx. 100 estudiantes por petición; CORS restringido por variable de entorno. | Abierta (HU-03) |
| B12 | El `batch` de HU-03 no define si reemplaza o fusiona. | Datos inconsistentes. | Upsert por `PK`+`SK`. | Abierta (HU-03) |
| B13 | Roles ausentes: el funcionario consultante (IES) no tiene autenticación. | Cualquiera con un token podría consultar. | Con `aud` en el JWT más `X-Node-API-Key` de la IES consultante, el token solo sirve a esa IES. Se aplica desde HU-06/07. | Abierta |

## C. Free Tier y costos (verificado)

| # | Hallazgo | Impacto | Acción | Estado |
|---|---|---|---|---|
| C1 | Desde el 15-jul-2025 las cuentas nuevas usan un plan basado en créditos: **plan Free (hasta 6 meses o hasta gastar USD 100-200 en créditos)**. El documento dice que API Gateway da 1M de peticiones "para siempre". No es así: ese 1M/mes aplica 12 meses a cuentas antiguas, y a cuentas nuevas se descuenta de créditos. Lambda (1M peticiones/mes) y DynamoDB (25 GB) sí son "siempre gratis". Fuentes: [Free Tier docs](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier.html), [anuncio AWS](https://aws.amazon.com/about-aws/whats-new/2025/07/aws-free-tier-credits-month-free-plan). | Costo cero no es "para siempre" en API Gateway. | Usar el **plan Free** en la cuenta (no se cobra; la cuenta se cierra al terminar). Alerta de presupuesto USD 0.01. Confirmar con el compañero qué tipo de cuenta tiene. | Abierta |
| C2 | Concurrencia reservada de 50 en Lambda: AWS exige dejar al menos 100 sin reservar. Cuentas nuevas pueden tener cuota total de 10, y entonces no se puede reservar nada. | `ReservedConcurrentExecutions: 50` fallaría el despliegue. | No fijarla en `template.yaml` por defecto. Poner como parámetro opcional. Revisar la cuota en consola. | Abierta |
| C3 | Cifrado en reposo con KMS (RNF). | Claves propias de KMS cuestan ~USD 1/mes. | DynamoDB cifra por defecto con una clave propiedad de AWS (sin costo). Se documenta como cumplimiento del RNF. No crear CMK. | Resuelta (propuesta) |
| C4 | CloudWatch Logs retiene logs indefinidamente. | Costo oculto a largo plazo. | `RetentionInDays: 7` en `template.yaml`. | Resuelta (propuesta) |
| C5 | Secrets Manager cobra. | Costo. | `JWT_SECRET` como variable de entorno de la Lambda (o SSM Parameter Store estándar). | Resuelta (propuesta) |
| C6 | DynamoDB: usar modo bajo demanda o aprovisionado. | Aprovisionado de 25 RCU/WCU entra en gratis; bajo demanda se factura por uso. | `PAY_PER_REQUEST` para tablas del proyecto: volumen mínimo, costo prácticamente nulo; si se prefiere cero absoluto, usar aprovisionado 1/1. Se decide en HU-01. | Abierta |

## D. Entorno y seguridad

| # | Descripción | Impacto | Solución simple propuesta | Estado |
|---|---|---|---|---|
| D1 | El secreto JWT de ejemplo está publicado en el documento. | Cualquiera puede forjar tokens. | Rotar: generar uno nuevo aleatorio y guardarlo solo en `.env` y en la Lambda. El valor por defecto de desarrollo es explícitamente inseguro. | Resuelta (propuesta) |
| D2 | Python local es 3.15.2; la Lambda usa 3.11. Pydantic y otras librerías pueden no tener wheels para 3.15. | `pip install` podría fallar o compilar. | Instalar Python 3.11 o 3.12 en todos los PCs. README lo indica. `.python-version` = 3.11. | Abierta |
| D3 | Sin SAM CLI no se puede probar `template.yaml` localmente. | Despliegue sin validar. | Compañero AWS instala SAM CLI. Se usa `sam validate` y `sam build`. | Abierta |
| D4 | El repo remoto existe (`BrayanBMC/RFHA-IES_SD_TGS`) pero está vacío. | Ninguno. | Primer push en la rama de HU-01 tras tu aprobación. | Cerrada |
| D5 | Pruebas de DynamoDB sin tocar AWS. | Costos y dependencia. | Repositorio en memoria como implementación principal para pruebas; `moto` solo para la implementación DynamoDB. | Resuelta (propuesta) |
| D6 | Mangum sobre HTTP API usa formato de evento v2; los endpoints deben incluir el stage correcto. | Rutas 404 en AWS. | Stage `$default` en `template.yaml` (sin prefijo de stage). | Resuelta (propuesta) |
