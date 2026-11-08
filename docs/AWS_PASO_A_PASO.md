# Guía AWS paso a paso

Para quien no conoce el código. Orden recomendado: el bloque 1 es la prioridad (demo del martes). Costo objetivo: USD 0.

> **Aviso de costos.** Las cuentas nuevas desde julio de 2025 tienen un *plan Free* (hasta 6 meses o hasta gastar los créditos de USD 100-200). Elige el plan **Free** al registrarte. Lambda y DynamoDB tienen cuota gratuita permanente. API Gateway se descuenta de los créditos en cuentas nuevas. Ver `docs/BRECHAS.md` C1.

---

## BLOQUE 1: Demo del martes (stack `rfha-demo`)

### Paso 1.1: Cuenta AWS
- **Objetivo:** tener una cuenta con plan Free.
- **Quién:** compañero AWS. **Dónde:** consola web (https://aws.amazon.com).
- **Pasos:**
  1. Crear la cuenta (o entrar a la existente).
  2. Si es nueva, elegir **Free account plan**.
  3. Verificar en *Billing and Cost Management → Free Tier* que aparece el plan.
- **Resultado esperado:** panel de Free Tier visible con créditos.
- **Si falla:** la tarjeta se rechaza → probar tarjeta con pagos internacionales. Cuenta antigua → seguir igual y vigilar el Paso 1.2.

### Paso 1.2: Alerta de presupuesto de USD 0.01
- **Objetivo:** enterarse de cualquier cobro.
- **Quién:** compañero AWS. **Dónde:** consola, *Billing → Budgets*.
- **Pasos:**
  1. *Create budget → Use a template → Zero spend budget*.
  2. Poner el correo del compañero y de Brayan.
  3. Crear.
- **Resultado esperado:** presupuesto "My Zero-Spend Budget" activo.
- **Si falla:** no aparece la opción → crear *Customized → Cost budget* de USD 0.01 mensual.

### Paso 1.3: Usuario IAM para desplegar
- **Objetivo:** no usar la cuenta raíz.
- **Quién:** compañero AWS. **Dónde:** consola, IAM.
- **Pasos:**
  1. *IAM → Users → Create user* → nombre `rfha-deployer`.
  2. Adjuntar políticas administradas: `AWSCloudFormationFullAccess`, `AWSLambda_FullAccess`, `AmazonAPIGatewayAdministrator`, `AmazonS3FullAccess`, `CloudWatchLogsFullAccess`, `IAMFullAccess`.
  3. *Security credentials → Create access key → Command Line Interface*. Guardar la clave en un gestor de contraseñas. **No subirla a git ni al chat.**
- **Resultado esperado:** Access Key ID y Secret.
- **Si falla:** `AccessDenied` al desplegar → falta una de las políticas anteriores. Para producción real se reduciría; para el prototipo académico es aceptable.

### Paso 1.4: Instalar AWS CLI y SAM CLI
- **Quién:** compañero AWS. **Dónde:** terminal.
- **Pasos (Windows):**
  1. `winget install Amazon.AWSCLI`
  2. `winget install Amazon.SAM-CLI`
  3. Cerrar y abrir la terminal. Comprobar: `aws --version` y `sam --version`.
- **Resultado esperado:** ambos muestran versión.
- **Si falla:** `comando no encontrado` → reiniciar la terminal. Sin winget → instaladores en la documentación de AWS.

### Paso 1.5: Configurar credenciales
- **Pasos:** `aws configure` → pegar Access Key, Secret, región `us-east-1`, formato `json`.
- **Resultado esperado:** `aws sts get-caller-identity` muestra la cuenta.
- **Si falla:** `InvalidClientTokenId` → clave mal copiada.

### Paso 1.6: Generar el secreto JWT
- **Quién:** Brayan. **Dónde:** terminal del proyecto.
- **Pasos:** `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Guardarlo en `.env` como `JWT_SECRET=...` y pasárselo al compañero por un canal privado.
- **Resultado esperado:** cadena de unos 64 caracteres.

### Paso 1.7: Desplegar la demo
- **Quién:** compañero AWS. **Dónde:** terminal, en la raíz del repo.
- **Pasos:**
  1. `sam build --template-file demo/template.yaml`
  2. `sam deploy --template-file .aws-sam/build/template.yaml --stack-name rfha-demo --resolve-s3 --capabilities CAPABILITY_IAM --parameter-overrides JwtSecret=<EL_SECRETO>`
  3. Al final, copiar el valor `ApiUrl` de los *Outputs*.
- **Resultado esperado:** `Successfully created/updated stack - rfha-demo`.
- **Si falla:**
  - `JwtSecret` demasiado corto → mínimo 32 caracteres.
  - `AccessDenied` → revisar políticas del Paso 1.3.
  - Falla con `python3.11` en `sam build` → instalar Python 3.11 o usar `sam build --use-container` (necesita Docker, evitar).

### Paso 1.8: Probar la demo desplegada
- **Quién:** Brayan. **Dónde:** terminal y Thunder Client.
- **Pasos:**
  1. `python scripts/check_demo.py <ApiUrl>` (con el mismo `JWT_SECRET` en `.env`).
  2. En Thunder Client, entorno `AWS`: poner `baseUrl` = `ApiUrl` y los tokens. Ejecutar las 3 requests.
- **Resultado esperado:** `TODO BIEN`; códigos 403, 403, 200.
- **Si falla:** 403 con token válido → el `JwtSecret` desplegado no coincide con el `.env`. 5xx → ver logs: `sam logs --stack-name rfha-demo`.

### Paso 1.9 (opcional): Despliegue desde GitHub Actions
- **Pasos:** en GitHub → *Settings → Secrets and variables → Actions*, crear `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` y `DEMO_JWT_SECRET`. Luego *Actions → CD demo (manual) → Run workflow*.
- **Nota:** nunca corre solo.

### Paso 1.10: Borrar todo (evitar costos)
- **Pasos:** `sam delete --stack-name rfha-demo`
- **Resultado esperado:** stack eliminado. Revisar en CloudFormation que no quede nada. El bucket S3 de SAM (`aws-sam-cli-managed-default...`) puede borrarse a mano si ya no se usa.

---

## BLOQUE 2: App final

Se agregan pasos por historia. El despliegue de la app final se arma con un `template.yaml` raíz cuando haya varias historias listas.

### HU-01: tabla de nodos
- **Objetivo:** guardar las solicitudes de registro de universidades.
- **Quién:** compañero AWS. **Dónde:** consola, DynamoDB.
- **Pasos:**
  1. *DynamoDB → Tables → Create table*.
  2. Nombre: `NodesTable`. Partition key: `node_id` (String). Sin sort key.
  3. Table settings: *Customize settings* → capacity mode **On-demand**. Dejar el cifrado por defecto (clave propiedad de AWS, sin costo).
  4. Crear.
- **Resultado esperado:** tabla `NodesTable` en estado Active.
- **Si falla:** nombre ya existe → usarlo tal cual o borrar la tabla vieja. Región distinta → crearla en `us-east-1`, igual que la Lambda.
- **Variables de la Lambda (cuando exista el despliegue de la app):** `REPOSITORY_BACKEND=dynamodb`, `NODES_TABLE=NodesTable`.
- **Permisos de la Lambda:** `dynamodb:PutItem`, `GetItem`, `Scan` sobre `NodesTable`.
- Por definir en próximas historias: `ADMIN_KEY` (HU-02), nuevas tablas.

### Interfaz web (frontend)
- **Nada nuevo en AWS.** La interfaz (HTML, CSS y JS) se sirve desde la misma Lambda y el mismo API Gateway; no se crean S3 ni CloudFront ni costos adicionales. En la demo, la página queda en la URL raíz (`ApiUrl`).
- Parámetro opcional `DemoMode` (`0` por defecto): con `1` la interfaz muestra los botones que generan tokens de prueba. Úsalo solo para ensayar y vuelve a desplegar con `0`. Ver `docs/DEMO.md`, sección 2.3.
