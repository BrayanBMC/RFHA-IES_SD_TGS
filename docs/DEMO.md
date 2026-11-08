# Demo del Middleware RFHA-IES

Guía para preparar, probar y exponer la demo. Está escrita para que cualquier persona del equipo la entienda, aunque no haya programado la aplicación. **Las pruebas se hacen en la pantalla, con clics, delante del público.** Los comandos solo se usan para preparar y, si algo falla, como respaldo (apéndice al final).

## Contenido

0. [La demo en 2 minutos](#0-la-demo-en-2-minutos)
1. [Conceptos explicados](#1-conceptos-explicados)
2. [Qué demuestra la demo](#2-qué-demuestra-la-demo)
3. [Plan A: levantar la demo en tu computador](#3-plan-a-levantar-la-demo-en-tu-computador)
4. [Plan B: levantar la demo en AWS](#4-plan-b-levantar-la-demo-en-aws)
5. [Conocer la pantalla](#5-conocer-la-pantalla)
6. [Casos de prueba en la pantalla](#6-casos-de-prueba-en-la-pantalla)
7. [Guion de la exposición (12 a 14 minutos)](#7-guion-de-la-exposición-12-a-14-minutos)
8. [Por qué cumple con la exposición y con la propuesta](#8-por-qué-cumple-con-la-exposición-y-con-la-propuesta)
9. [Cómo funciona el código](#9-cómo-funciona-el-código)
10. [Preguntas probables de los docentes](#10-preguntas-probables-de-los-docentes)
11. [Si algo falla en vivo](#11-si-algo-falla-en-vivo)
12. [Apéndice: respaldo con comandos](#12-apéndice-respaldo-con-comandos)

---

## 0. La demo en 2 minutos

**Qué es.** Una página web donde un funcionario de una universidad pide el historial académico de un estudiante. El sistema **solo lo entrega si el estudiante dio permiso**. Ese permiso es un código especial llamado *token*.

**Qué se ve.** Una pantalla con tres zonas: arriba a la izquierda llenas la solicitud, arriba a la derecha ves cuatro controles de seguridad que se ponen en verde o en rojo, y abajo aparece la respuesta con el expediente.

**Cómo se prueba.** Eliges un estudiante de una lista, pulsas el botón **Token válido** (simula que el estudiante dio permiso) y luego **Consultar expediente**. Para mostrar los rechazos pulsas **Sin token** o **Token expirado**. Todo con clics.

**Dos formas de correrla** (con el mismo código):
- **Plan A, en tu computador.** No necesita internet. Se levanta con un solo comando.
- **Plan B, en AWS.** Queda en internet con una dirección pública. La despliega el compañero que maneja AWS.

**Dos reglas para no perderse:**
1. Todos los datos son **ficticios**. No hay personas reales.
2. Si algo falla en vivo, pasa al otro plan (sección 11).

---

## 1. Conceptos explicados

Cada concepto que aparece en este documento está aquí, con un ejemplo de la demo.

### Sobre el problema

| Concepto | Qué es, en simple | En la demo |
|---|---|---|
| **IES** | Institución de Educación Superior: una universidad. | Distrital, Nacional, Javeriana y Andes. |
| **Historial académico** | El registro de un estudiante: materias, notas, créditos y promedio. | El expediente que aparece al consultar. |
| **Homologación** | Cuando una universidad reconoce las materias que el estudiante ya aprobó en otra, para no repetirlas. Hoy tarda semanas por trámites en papel. | El panel «Apoyo a la homologación». |
| **Créditos** | Medida del peso de una materia y del avance de la carrera. Una carrera suma un total de créditos. | «140 de 160 créditos». |
| **Nota y promedio acumulado** | La nota va de 0,0 a 5,0 y **se aprueba con 3,0 o más**. El promedio acumulado resume todas las notas del estudiante. | «Promedio 4,52». |
| **Nota mínima aceptada** | La nota por debajo de la cual la universidad que recibe no homologa una materia. Cada universidad fija la suya. | El campo del panel de homologación. |
| **Red federada** | Varias universidades conectadas **sin juntar sus datos en un solo lugar**. Cada una guarda los suyos; la red solo permite consultarlos con permiso. | Los 4 «nodos» de la demo. |
| **Nodo** | Cada universidad dentro de la red, con su propia base de datos. | «Universidad de origen» en el expediente. |

### Sobre la seguridad

| Concepto | Qué es, en simple | En la demo |
|---|---|---|
| **Consentimiento** | El permiso explícito del estudiante para que otra universidad vea su historial. | El token. |
| **Token** | Un texto largo y raro que funciona como una **llave temporal**. Quien lo presenta demuestra que el estudiante lo autorizó. | El campo «Token de consentimiento». |
| **JWT** | El formato del token. Lleva dentro quién es el estudiante y cuándo vence, y va firmado. Se lee «yot». | Los tokens que genera la demo. |
| **Firma y secreto** | El token se firma con una clave que solo conoce el sistema, el **secreto**. Es como un sello: si alguien cambia una sola letra del token, el sello deja de coincidir y se rechaza. | La escena «Token alterado». |
| **Vigencia / expiración** | El token **caduca**. Pasada la fecha, ya no sirve. Los de la demo duran 24 horas. | El botón «Token expirado». |
| **Titular del consentimiento** | El token pertenece a **un** estudiante. Con el permiso de Laura no se puede ver a Valentina. | La escena «Token de otra persona». |
| **Variable de entorno** | Un valor secreto que se entrega al programa desde fuera, sin escribirlo en el código. Así el secreto no queda en GitHub. | `JWT_SECRET`. |

### Sobre la comunicación entre programas

| Concepto | Qué es, en simple | En la demo |
|---|---|---|
| **Middleware** | Un programa **intermediario** entre el que pide (la universidad que consulta) y quien guarda los datos. Revisa los permisos, busca el dato y lo entrega siempre en el mismo formato. | Todo lo que hay detrás de la pantalla. |
| **Web service** (servicio web) | Una forma de que dos programas se hablen por internet usando reglas estándar. | La dirección que consulta la pantalla. |
| **API REST** | Un tipo de servicio web: se pide algo a una dirección (URL) y se recibe una respuesta. | `/api/v1/federated/academic-history/{código}` |
| **JSON** | El formato de texto en que viaja la respuesta: pares «nombre: valor». Lo entienden todos los lenguajes. | El recuadro «Ver respuesta JSON». |
| **HTTP y códigos de estado** | Es el idioma de la web. Cada respuesta trae un número: **200** = todo bien; **403** = «te reconozco, pero no tienes permiso»; **404** = «eso no existe». | La insignia «HTTP 200», «HTTP 403», «HTTP 404». |
| **Transparencia de acceso** | Todas las universidades se consultan **de la misma manera**, sin importar cómo guarde cada una sus datos. | El mismo formulario para las 4 universidades. |
| **Transparencia de ubicación** | Quien consulta **no sabe dónde** están los datos (qué servidor, qué ciudad). Solo conoce una dirección. | Una única página para todo. |

### Sobre AWS y la ejecución

| Concepto | Qué es, en simple | En la demo |
|---|---|---|
| **AWS** | La nube de Amazon: computadores que se alquilan por internet. | Plan B. |
| **Serverless** | «Sin servidores que administrar»: Amazon enciende el programa **solo cuando llega una petición** y lo apaga después. | Todo el Plan B. |
| **Lambda** | El servicio de AWS que ejecuta nuestro programa bajo demanda. | La función `rfha-demo`. |
| **API Gateway** | La «puerta de entrada» pública de AWS. Recibe las peticiones de internet y las pasa a la Lambda. | La URL `https://....execute-api...amazonaws.com`. |
| **DynamoDB** | La base de datos de AWS. | En la demo **no se usa**: los datos están en un archivo del programa. En el proyecto final sí. |
| **Arranque en frío (cold start)** | Si la Lambda lleva rato sin usarse, la primera petición tarda 1 a 3 segundos en despertar. Es normal. | Haz una consulta de prueba antes de exponer. |
| **Free Tier / plan Free** | Capa gratuita de AWS: dentro de ciertos límites no se cobra. | Costo de la demo: USD 0. |
| **localhost y puerto** | `127.0.0.1` (o `localhost`) significa «este mismo computador». El puerto (`:8000`) es la puerta por la que responde el programa. | `http://127.0.0.1:8000` |
| **Terminal** | Ventana donde se escriben comandos. Se usa solo para preparar. | PowerShell en VS Code. |

---

## 2. Qué demuestra la demo

```
 Funcionario (navegador)
        |  Pide el historial del estudiante 20262678029
        |  y presenta el token del estudiante
        v
 +------------------------------------------------+
 |  MIDDLEWARE  (API Gateway + Lambda en AWS)     |
 |                                                |
 |  1. ¿Llegó el token?                no -> 403  |
 |  2. ¿Firma buena y no vencido?      no -> 403  |
 |  3. ¿Es el token de ESTE estudiante? no -> 403 |
 |  4. ¿Existe el estudiante?          no -> 404  |
 |  5. Entrega el historial en JSON       -> 200  |
 +------------------------------------------------+
        |
        v
 Datos de las universidades (en la demo: simulados en memoria)
```

Estos cuatro controles son exactamente los cuatro pasos que se iluminan en la pantalla.

| Escenario | Resultado |
|---|---|
| Sin token | **403**: acceso denegado |
| Token vencido, alterado o falso | **403**: acceso denegado |
| Token de otro estudiante | **403**: acceso denegado |
| Estudiante que no existe | **404**: no encontrado |
| Token válido del estudiante | **200**: se entrega el expediente |

---

## 3. Plan A: levantar la demo en tu computador

**Necesitas:** Python 3.11 o 3.12 instalado y el proyecto descargado. No necesitas internet, AWS ni cuenta alguna.

### 3.1 Un solo comando

Abre una terminal de VS Code en la carpeta del proyecto (`Ctrl+ñ`) y escribe:

```powershell
.\run-demo.cmd
```

En macOS o Linux: `bash run-demo.sh`. Si usas VS Code, también sirve `Ctrl+Shift+P`, escribir *Tasks: Run Task* y elegir **Demo: levantar en local**.

**Qué hace por ti:** crea un espacio de trabajo aislado para Python, instala lo necesario, crea el secreto, enciende la demo, prueba por su cuenta los tres escenarios básicos y te dice cuando está lista.

**La primera vez tarda 1 a 2 minutos**; las siguientes, segundos. Sabrás que salió bien cuando veas:

```
RESULTADO: TODO BIEN
DEMO LISTA
  Interfaz web:   http://127.0.0.1:8000   <- abre esta en el navegador
```

### 3.2 Abrir la pantalla

Abre el navegador en **http://127.0.0.1:8000**. Arriba a la derecha debe decir **Entorno: Local**.

> **No cierres la terminal** mientras expones: es la que mantiene la demo encendida. Para apagarla, `Ctrl+C`.

### 3.3 Si no funciona

- «La ejecución de scripts está deshabilitada»: usa `.\run-demo.cmd` (ya evita ese bloqueo).
- «El puerto 8000 está ocupado»: `.\run-demo.cmd -Port 8010` y abre `http://127.0.0.1:8010`.
- Falla al instalar: instala Python 3.12 (con Python 3.14 o más nuevo puede fallar).

---

## 4. Plan B: levantar la demo en AWS

Esta parte la hace **el compañero que maneja AWS**. No necesita entender el código ni abrir otro documento: todo está aquí.

### 4.0 Resumen

| | |
|---|---|
| **Qué se crea** | Un paquete llamado **`rfha-demo`** con una función Lambda (el programa), una puerta de entrada (API Gateway) y un registro de actividad que se borra a los 7 días. **No usa base de datos.** |
| **Qué se obtiene** | Una dirección pública `https://xxxxxxxx.execute-api.us-east-1.amazonaws.com`. Al abrirla aparece **la misma pantalla** de la demo. |
| **Qué necesita de Brayan** | Un **secreto**: un texto de más de 32 caracteres (paso 7). |
| **Costo** | USD 0 dentro del Free Tier. |
| **Tiempo** | 30 a 45 minutos la primera vez. |
| **Quién hace qué** | Compañero de AWS: pasos 1 a 10. Brayan: da el secreto (paso 7) y prueba al final (paso 11). |

### 4.1 Una decisión importante: el modo demostración

La pantalla tiene unos botones, **Token válido**, **Token expirado** y **Sin token**, que **simulan al estudiante** para poder hacer las pruebas con clics. Esos botones solo aparecen si la demo se despliega con **`DemoMode=1`**.

| Valor | Qué pasa | Cuándo usarlo |
|---|---|---|
| `DemoMode=1` | Aparecen los botones y la lista de estudiantes. **Cualquiera que conozca la dirección podría generar tokens**, es decir, la protección queda desactivada para quien tenga la URL. | **Para la exposición**, que es temporal. La dirección es larga y aleatoria. **Después de exponer, se borra todo** (paso 13). |
| `DemoMode=0` | No aparecen los botones; solo se puede probar pegando tokens hechos a mano. | Si la demo va a quedar publicada mucho tiempo. |

**Recomendación para la exposición: `DemoMode=1` y borrar el paquete al terminar.** En el paso 9 se indica exactamente dónde se escribe.

### 4.2 Qué necesita tener el compañero
- Un computador con **Windows y PowerShell**, con internet.
- Una **tarjeta** con pagos internacionales (AWS la pide para crear la cuenta, aunque no cobre).
- Permiso para instalar programas.

### 4.3 Paso a paso

#### Paso 1. Crear o verificar la cuenta AWS
*Una cuenta AWS es el «usuario principal» donde viven todos los servicios y se factura el consumo.*
- **Dónde:** navegador, https://aws.amazon.com
- **Pasos:**
  1. Pulsa *Crear una cuenta de AWS* (o entra con la cuenta que ya existe).
  2. Si la cuenta es nueva y pregunta por el plan, elige **Free account plan** (plan gratuito). **No** elijas *Paid plan*.
  3. En la consola, abre *Billing and Cost Management* y luego *Free Tier*. Debe aparecer el plan y el saldo de créditos.
  4. Arriba a la derecha elige la región **US East (N. Virginia) us-east-1**. *(Una región es la ubicación geográfica de los servidores.)*
- **Resultado esperado:** ves el panel de Free Tier y la región `us-east-1`.
- **Si falla:** si rechazan la tarjeta, prueba otra con pagos internacionales habilitados.

#### Paso 2. Alerta de gasto de USD 0.01
*Es una red de seguridad: AWS te escribe un correo si se cobra aunque sea un centavo.*
- **Dónde:** consola web, *Billing and Cost Management*, *Budgets*.
- **Pasos:** *Create budget*, *Use a template (simplified)*, **Zero spend budget**; escribe los correos del compañero y de Brayan; *Create budget*.
- **Resultado esperado:** aparece «My Zero-Spend Budget» activo.
- **Si falla:** si no aparece la plantilla, crea un *Customized (advanced)*, *Cost budget* mensual de USD 0.01.

#### Paso 3. Crear un usuario para desplegar
*IAM es el servicio de usuarios y permisos de AWS. Se crea un usuario solo para esta tarea en lugar de usar la cuenta principal, que es más peligrosa.*
- **Dónde:** consola web, *IAM*, *Users*.
- **Pasos:**
  1. *Create user*, nombre `rfha-deployer`, *Next*.
  2. *Attach policies directly* y marca estas **6 políticas** *(una política es un permiso)*: `AWSCloudFormationFullAccess`, `AWSLambda_FullAccess`, `AmazonAPIGatewayAdministrator`, `AmazonS3FullAccess`, `CloudWatchLogsFullAccess`, `IAMFullAccess`.
  3. *Create user*.
  4. Abre el usuario, pestaña *Security credentials*, *Create access key*, caso de uso **Command Line Interface (CLI)**, confirma y *Create access key*.
  5. Copia el **Access key ID** y el **Secret access key** a un gestor de contraseñas. *(Son el usuario y la contraseña del programa; el secreto solo se muestra una vez.)*
- **Resultado esperado:** tienes las dos claves del usuario `rfha-deployer`.
- **Si falla:** si luego sale `AccessDenied`, falta alguna de las 6 políticas. **Nunca** subas estas claves a GitHub ni las pegues en chats.

#### Paso 4. Instalar las herramientas
*AWS CLI y SAM son los programas con los que se habla con AWS desde la terminal. Python 3.11 es la versión que usa la Lambda. Git descarga el código.*
- **Dónde:** PowerShell (ábrelo nuevo).
- **Pasos:**
  ```powershell
  winget install Amazon.AWSCLI
  winget install Amazon.SAM-CLI
  winget install Python.Python.3.11
  winget install Git.Git
  ```
  Cierra PowerShell, ábrelo de nuevo y comprueba:
  ```powershell
  aws --version
  sam --version
  py -3.11 --version
  git --version
  ```
- **Resultado esperado:** los cuatro muestran una versión (`py -3.11` dice `Python 3.11.x`).
- **Si falla:** «comando no encontrado» significa que no cerraste y reabriste PowerShell. Sin `winget`, descarga los instaladores de las páginas oficiales de AWS CLI, AWS SAM CLI, python.org y git-scm.com. **Python 3.11 es obligatorio.**

#### Paso 5. Conectar la terminal con la cuenta
- **Dónde:** PowerShell.
- **Pasos:**
  ```powershell
  aws configure
  ```
  Responde: *AWS Access Key ID* y *AWS Secret Access Key* con las del paso 3; *Default region name* `us-east-1`; *Default output format* `json`. Luego:
  ```powershell
  aws sts get-caller-identity
  ```
- **Resultado esperado:** devuelve un texto con tu número de cuenta y un `Arn` que termina en `user/rfha-deployer`.
- **Si falla:** `InvalidClientTokenId` o `SignatureDoesNotMatch` significa que copiaste mal una clave; repite `aws configure`.

#### Paso 6. Descargar el código
- **Dónde:** PowerShell.
- **Pasos:**
  ```powershell
  git clone https://github.com/BrayanBMC/RFHA-IES_SD_TGS.git
  cd RFHA-IES_SD_TGS
  ```
  Si Brayan indica que lo último aún está en la rama `dev`, escribe además: `git checkout dev`.
- **Resultado esperado:** al escribir `dir demo` aparecen los archivos `main.py`, `students.py` y `template.yaml`.
- **Si falla:** `repository not found` significa que Brayan debe darte acceso al repositorio.

#### Paso 7. Obtener el secreto
*El secreto es la «tinta» con la que se firman los tokens. Sin él, nadie puede fabricar un token válido. Lo conocen solo Brayan y la Lambda.*
- **Quién:** Brayan lo genera y se lo pasa al compañero **por un mensaje privado** (no por un grupo).
- **Cómo se genera:**
  ```powershell
  py -3.11 -c "import secrets; print(secrets.token_urlsafe(48))"
  ```
  Imprime un texto de unos 64 caracteres. Ese texto es el secreto.
- **Para el compañero:** guárdalo en una variable de la terminal (vive mientras la terminal esté abierta):
  ```powershell
  $secreto = "PEGA_AQUI_EL_SECRETO"
  ```
- **Reglas:** mínimo 32 caracteres. Brayan lo guarda también en su archivo `.env` como `JWT_SECRET=...`. No se sube a GitHub.

#### Paso 8. Construir el paquete
*«Construir» (build) es empaquetar el programa con todo lo que necesita para subirlo a AWS.*
- **Dónde:** PowerShell, dentro de la carpeta `RFHA-IES_SD_TGS`.
- **Comando:**
  ```powershell
  sam build --template-file demo/template.yaml
  ```
- **Resultado esperado:** al final dice `Build Succeeded`.
- **Si falla:** «Binary validation failed for python» significa que Python 3.11 no está instalado: repite el paso 4 y reabre PowerShell. «template.yaml not found» significa que no estás en la carpeta del proyecto.

#### Paso 9. Desplegar
*Desplegar es subir el paquete a AWS y dejarlo funcionando. SAM lo hace creando un «stack» (un conjunto de recursos que se crean y se borran juntos).*
- **Dónde:** misma terminal (con `$secreto` definido).
- **Comando para la exposición (con botones de simulación):**
  ```powershell
  sam deploy --template-file .aws-sam/build/template.yaml --stack-name rfha-demo --resolve-s3 --capabilities CAPABILITY_IAM --region us-east-1 --no-confirm-changeset --no-fail-on-empty-changeset --parameter-overrides "JwtSecret=$secreto" "DemoMode=1"
  ```
  Para desplegar **sin** botones de simulación cambia `"DemoMode=1"` por `"DemoMode=0"`.
- **Resultado esperado:** tarda 2 a 4 minutos y termina con `Successfully created/updated stack - rfha-demo`. En *Outputs* aparece:
  ```
  Key    ApiUrl
  Value  https://abc123xyz.execute-api.us-east-1.amazonaws.com
  ```
- **Si falla:**
  - `AccessDenied`: falta una política del paso 3.
  - Error con `JwtSecret`: el secreto tiene menos de 32 caracteres.
  - `ROLLBACK_COMPLETE`: en la consola web, *CloudFormation*, stack `rfha-demo`, pestaña *Events* está el motivo. Para reintentar, borra el fallido (`sam delete --stack-name rfha-demo --region us-east-1`) y repite este paso.
  - `The security token ... is invalid`: repite el paso 5.

#### Paso 10. Comprobar en el navegador
- **Dónde:** navegador.
- **Pasos:**
  1. Copia el `Value` de `ApiUrl`. Si se perdió: `aws cloudformation describe-stacks --stack-name rfha-demo --region us-east-1 --query "Stacks[0].Outputs"`.
  2. Ábrelo en el navegador. Debe aparecer la pantalla **«Consulta federada de historial académico»** y arriba a la derecha **Entorno: Nube (AWS)**.
  3. En *Estudiante de ejemplo* elige **Brayan Acosta Parrado**, pulsa **Token válido** y luego **Consultar expediente**.
- **Resultado esperado:** los cuatro controles se ponen en verde, la insignia dice **HTTP 200** y aparece el expediente.
- **Si falla:**
  - No aparecen los botones ni la lista: se desplegó con `DemoMode=0`. Repite el paso 9 con `DemoMode=1`.
  - Pantalla con `{"message":"Internal Server Error"}`: error dentro de la Lambda; mira los logs (sección 4.5).
  - La primera carga tarda 1 a 3 segundos: es el arranque en frío, normal.

#### Paso 11. Prueba completa de Brayan
Con la URL de AWS, Brayan repite en la pantalla las escenas 1, 2, 3, 4 y 6 de la sección 6. Si todas dan lo esperado, la demo está lista.

#### Paso 12. Entregar la URL
El compañero envía a Brayan **la URL** y confirma con qué valor de `DemoMode` desplegó. Brayan la abre en una pestaña antes de exponer.

#### Paso 13. Borrar todo al terminar (importante)
*Borrar evita costos y, con `DemoMode=1`, cierra la puerta que permite generar tokens.*
```powershell
sam delete --stack-name rfha-demo --region us-east-1
```
Responde `y` a las preguntas. Después, en la consola web, *S3*: borra el bucket que empieza por `aws-sam-cli-managed-default`. Finalmente, en *IAM*, desactiva o elimina la access key de `rfha-deployer`.

### 4.4 Despliegue alternativo desde GitHub (opcional)
Evita instalar SAM en el computador. En el repositorio de GitHub:
1. *Settings*, *Secrets and variables*, *Actions*, *New repository secret*. Crea tres: `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY` (las del paso 3) y `DEMO_JWT_SECRET` (el secreto del paso 7).
2. Pestaña *Actions*, flujo **CD demo (manual)**, *Run workflow*.
3. La URL queda en la consola web de CloudFormation, stack `rfha-demo`, pestaña *Outputs*.

Este flujo despliega con `DemoMode=0`. Para la exposición con botones usa el paso 9.

### 4.5 Ver los logs si algo falla
```powershell
sam logs --stack-name rfha-demo --region us-east-1
```
O en la consola web: *CloudWatch*, *Log groups*, `/aws/lambda/rfha-demo`.

### 4.6 Actualizar la demo si Brayan cambia el código
Repite los pasos 6 (`git pull`), 8 y 9 con el mismo secreto. La URL no cambia.

---

## 5. Conocer la pantalla

```
+----------------------------------------------------------------------+
|  RFHA-IES                                       Entorno: Local       |
+----------------------------------------------------------------------+
|  Consulta federada de historial académico                            |
|                                                                      |
|  +----------------------------+  +--------------------------------+  |
|  | 1. SOLICITUD               |  | 2. VALIDACIÓN DEL MIDDLEWARE   |  |
|  |  Estudiante de ejemplo [v] |  |  (1) Token presente            |  |
|  |  Código del estudiante [ ] |  |  (2) Firma y vigencia          |  |
|  |  Token de consentimiento   |  |  (3) Titular del consentimiento|  |
|  |  [                       ] |  |  (4) Búsqueda del expediente   |  |
|  |  Simular al estudiante:    |  |                                |  |
|  |  [Token válido]            |  |  Cada uno: Pendiente /         |  |
|  |  [Token expirado]          |  |  Aprobado / Rechazado / Omitido|  |
|  |  [Sin token]               |  +--------------------------------+  |
|  |  [Consultar expediente]    |                                      |
|  +----------------------------+                                      |
|  +----------------------------------------------------------------+  |
|  | 3. RESPUESTA                                                   |  |
|  |  [HTTP 200]  Acceso concedido...                               |  |
|  |  Nombre · estado · universidad · programa · promedio · títulos |  |
|  |  Avance de créditos  ████████░░  140 de 160                    |  |
|  |  Apoyo a la homologación: Nota mínima aceptada [3.5]           |  |
|  |  Tabla de asignaturas por semestre                             |  |
|  |  > Ver respuesta JSON      [Copiar como curl]                  |  |
|  +----------------------------------------------------------------+  |
+----------------------------------------------------------------------+
```

### Zona 1. Solicitud (lo que llenas)

| Elemento | Qué es y qué poner |
|---|---|
| **Estudiante de ejemplo** | Lista desplegable con los 6 estudiantes ficticios. Al elegir uno, **se completa solo el código**. Solo aparece en modo demostración. |
| **Código del estudiante** | El identificador de la persona (por ejemplo `20262678029`). Acepta letras, números, guion y guion bajo, hasta 32 caracteres. Para probar un estudiante que no existe, escribe `12345`. |
| **Token de consentimiento** | El permiso del estudiante. Normalmente se llena solo al pulsar un botón; también puedes pegar o editar uno a mano. Vacío significa «sin permiso». |
| **Token válido** | Crea un permiso vigente por 24 horas **para el código que esté escrito en ese momento**. |
| **Token expirado** | Crea un permiso que ya venció, para el código escrito. |
| **Sin token** | Borra el campo del token. |
| **Consultar expediente** | Envía la solicitud. Úsalo siempre al final. |

> **Dato clave:** los botones de token firman **para el código que esté escrito en ese instante**. Si cambias el código después, el token seguirá siendo del primero. Eso se aprovecha en la escena 6.

### Zona 2. Validación del middleware (se ilumina sola)

Cuatro controles que se revisan en orden. Si uno falla, los siguientes quedan «Omitido», porque el sistema ya cortó.

| Control | Qué revisa |
|---|---|
| **1. Token presente** | Que se haya enviado un token. |
| **2. Firma y vigencia** | Que el token no esté alterado y no haya vencido. |
| **3. Titular del consentimiento** | Que el token sea de **ese** estudiante. |
| **4. Búsqueda del expediente** | Que el estudiante exista en la red. |

### Zona 3. Respuesta

| Elemento | Qué muestra |
|---|---|
| **Insignia HTTP** | `HTTP 200` (verde) si se entregó el expediente; `HTTP 403` o `HTTP 404` (rojo) si se rechazó. |
| **Mensaje** | La razón en palabras. |
| **Tarjeta del estudiante** | Nombre, estado (Activo, Graduado o Retirado), universidad de origen, programa, promedio acumulado y, si aplica, título y fecha de grado. |
| **Avance de créditos** | Barra con créditos aprobados sobre el total de la carrera. |
| **Apoyo a la homologación** | Campo **Nota mínima aceptada**. Al cambiarlo, la tabla resalta en verde las materias **aprobadas con esa nota o más** («candidata») y una frase resume cuántas son y cuántos créditos suman. |
| **Tabla por semestre** | Semestre, código, asignatura, créditos, nota y estado (Aprobada, Reprobada o En curso). |
| **Ver respuesta JSON** | Muestra el texto crudo que devolvió el servicio. Sirve para enseñar qué es una API. |
| **Copiar como curl** | Copia el comando equivalente. Es opcional. |

---

## 6. Casos de prueba en la pantalla

Todos se hacen **con clics, delante del público**. Cada escena indica: qué clics dar, qué se ve y qué decir.

### 6.1 Los 6 estudiantes de la demo (datos ficticios)

| Código | Estudiante | Universidad | Programa | Estado | Promedio | Créditos | Sirve para |
|---|---|---|---|---|---|---|---|
| `20262678029` | **Brayan Acosta Parrado** | Distrital | Ingeniería en Telemática | Activo | 4,52 | 140 de 160 | Caso principal, rechazos y AWS. 8 materias, una en curso. |
| `20251234501` | **Laura Camila Ríos Herrera** | Nacional | Ingeniería de Sistemas y Computación | Activo | 4,18 | 118 de 160 | **Homologación**: reprobó Cálculo Integral (2,6) y lo repitió (3,4). |
| `20241122002` | **Andrés Felipe Moreno Castro** | Javeriana | Ingeniería Electrónica | **Graduado** | 4,05 | 168 de 168 | Título y fecha de grado. |
| `20231098763` | **Valentina Torres Quintero** | Andes | Economía | Activo | 4,62 | 90 de 140 | Promedio alto. |
| `20221050914` | **Juan Sebastián Pardo Gil** | Distrital | Ingeniería Industrial | **Retirado** | 3,21 | 64 de 160 | Promedio bajo y materias repetidas. |
| `20252345678` | **María Fernanda Ospina Duarte** | Nacional | Estadística | Activo | 3,88 | 52 de 150 | Primeros semestres. |

### 6.2 Antes de empezar cada escena
Recarga la página (`F5`) para dejar todo limpio, salvo que la escena diga lo contrario.

### Escenas de seguridad (los rechazos)

#### Escena 1. Consulta exitosa
- **Objetivo:** mostrar el camino feliz.
- **Clics:**
  1. En *Estudiante de ejemplo* elige **Brayan Acosta Parrado**.
  2. Pulsa **Token válido**. El campo del token se llena.
  3. Pulsa **Consultar expediente**.
- **Qué se ve:** los 4 controles en **verde**, insignia **HTTP 200**, mensaje «Acceso concedido: el estudiante autorizó la consulta». Aparece Brayan (Activo), promedio 4,52, «140 de 160 (88 %)» y 8 materias; la última, «En curso».
- **Qué decir:** «El estudiante dio su permiso; el middleware verificó cuatro cosas y entregó el expediente casi al instante».
- **Extra:** abre *Ver respuesta JSON* y explica que eso es lo que viaja por la red.

#### Escena 2. Sin token
- **Clics:** Brayan elegido, pulsa **Sin token** (el campo del token queda vacío) y **Consultar expediente**.
- **Qué se ve:** **HTTP 403**, mensaje «ACCESO DENEGADO: falta el token de consentimiento del estudiante». Control 1 en **rojo** y controles 2, 3 y 4 en «Omitido». **No aparece ningún dato.**
- **Qué decir:** «Sin permiso no hay acceso, y el sistema ni siquiera busca el expediente».

#### Escena 3. Token expirado
- **Clics:** Brayan elegido, pulsa **Token expirado** y **Consultar expediente**.
- **Qué se ve:** **HTTP 403**, «El token de consentimiento ha expirado». Control 1 verde, control 2 **rojo**, 3 y 4 «Omitido».
- **Qué decir:** «El permiso caduca. Un token viejo ya no sirve aunque sea auténtico».

#### Escena 4. Token alterado
- **Clics:** Brayan elegido, pulsa **Token válido**. Luego haz clic dentro del recuadro del token y borra **una letra del final** (tecla Retroceso). Pulsa **Consultar expediente**.
- **Qué se ve:** **HTTP 403**, «ACCESO DENEGADO: token de consentimiento inválido». Control 2 rojo.
- **Qué decir:** «Alguien intentó manipular el token. Cambiar una sola letra rompe la firma y el sistema lo detecta».

#### Escena 5. Texto que no es un token
- **Clics:** Brayan elegido. En el recuadro del token escribe `esto-no-es-un-token` y pulsa **Consultar expediente**.
- **Qué se ve:** **HTTP 403**, «token de consentimiento inválido». Control 2 rojo.
- **Qué decir:** «Inventar un token tampoco funciona: no tiene la firma del sistema».

#### Escena 6. El token es de una persona
- **Objetivo:** mostrar privacidad entre estudiantes.
- **Clics:**
  1. Elige **Laura Camila Ríos Herrera**.
  2. Pulsa **Token válido** (es el permiso de Laura).
  3. **Sin tocar el token**, elige ahora **Valentina Torres Quintero** en la lista.
  4. Pulsa **Consultar expediente**.
- **Qué se ve:** **HTTP 403**, «ACCESO DENEGADO: el token no autoriza a este estudiante». Controles 1 y 2 verdes, control 3 **rojo**.
- **Qué decir:** «El permiso de Laura sirve para ver a Laura, no a Valentina. Cada estudiante decide quién ve sus datos».

#### Escena 7. Estudiante que no existe
- **Clics:**
  1. En *Código del estudiante* escribe `12345` (no uses la lista).
  2. Pulsa **Token válido** (se firma para `12345`).
  3. Pulsa **Consultar expediente**.
- **Qué se ve:** **HTTP 404**, «Estudiante no encontrado en la red federada». Controles 1, 2 y 3 **verdes**, control 4 **rojo**.
- **Qué decir:** «El permiso es válido, pero esa persona no existe. El sistema distingue "no tienes permiso" (403) de "no existe" (404)».

#### Escena 8. Código mal escrito
- **Clics:** en *Código del estudiante* escribe `abc def` (con espacio) y pulsa **Consultar expediente**.
- **Qué se ve:** un mensaje rojo bajo el campo: «Escribe un código válido: solo letras, números, guion o guion bajo (máximo 32)». **No se envía nada** al servidor. Prueba también con el campo vacío.
- **Qué decir:** «La pantalla valida lo escrito antes de enviarlo».

### Escenas de la red federada y la homologación

#### Escena 9. Tres universidades, una sola pantalla
- **Objetivo:** transparencia de acceso y de ubicación.
- **Clics:** repite los pasos de la escena 1 (elegir, **Token válido**, **Consultar expediente**) con **Laura** (Nacional), **Andrés Moreno** (Javeriana) y **Valentina Torres** (Andes). No hace falta recargar entre una y otra.
- **Qué se ve:** cada vez cambia «Universidad de origen», pero el formato, los cuatro controles y la forma de consultar son idénticos.
- **Qué decir:** «Son tres universidades distintas. La persona que consulta usa lo mismo y no sabe dónde viven los datos. Esa es la transparencia de acceso y de ubicación».

#### Escena 10. Homologación con Laura
- **Objetivo:** el uso real: decidir qué materias reconocer.
- **Clics:** consulta a **Laura** (como en la escena 1). Baja a *Apoyo a la homologación*. Con **3,5** en *Nota mínima aceptada* lee la frase. Cambia el valor a **4,0** y vuelve a leerla.
- **Qué se ve:**
  - Con 3,5: «**8 de 9** asignaturas aprobadas tienen nota de 3,5 o más: **25 créditos** candidatos a homologar». Las filas candidatas se pintan en verde y dicen «candidata».
  - Con 4,0: «**7 de 9** … **21 créditos**». Queda fuera Física Mecánica (3,9).
  - Cálculo Integral aparece dos veces: 2024-2 en rojo «Reprobada» (2,6) y 2025-1 «Aprobada» (3,4), que **no** es candidata con 3,5.
  - La materia de 2026-2 dice «En curso» y no cuenta.
- **Qué decir:** «Cada universidad fija su criterio. Antes esto tomaba semanas de papeleo; aquí se ve en segundos qué se puede reconocer».

#### Escena 11. Un graduado (Andrés)
- **Clics:** elige **Andrés Felipe Moreno Castro**, **Token válido**, **Consultar expediente**.
- **Qué se ve:** estado **Graduado**, además aparecen *Título* («Ingeniero Electrónico») y *Fecha de grado* («2025-12-12»). Créditos «168 de 168 (100 %)». Con nota mínima 3,5: 6 de 6 (20 créditos); con 4,0: 5 de 6 (16 créditos).
- **Qué decir:** «El mismo servicio atiende egresados: sirve para verificar un título sin pedir un certificado».

#### Escena 12. Un retirado (Juan)
- **Clics:** elige **Juan Sebastián Pardo Gil**, **Token válido**, **Consultar expediente**.
- **Qué se ve:** estado **Retirado** (en rojo), promedio 3,21, «64 de 160 (40 %)». Dos materias reprobadas: Física I (2,8) y Probabilidad (2,9); Física I aparece repetida y aprobada (3,4). Con nota mínima 3,5: **2 de 6** candidatas (Química General y Dibujo Técnico, **5 créditos**).
- **Qué decir:** «Un estudiante que se va y quiere continuar en otra universidad: el sistema deja ver con honestidad qué se le puede reconocer».

#### Escena 13. Promedio alto y primeros semestres
- **Clics:** consulta a **Valentina** (promedio 4,62) y luego a **María Ospina** (52 de 150 créditos, 35 %).
- **Qué se ve:** con nota mínima 4,5, Valentina tiene **7 de 8** candidatas (22 créditos; Econometría I con 4,4 queda fuera). María tiene **8 de 8** con 3,5 (26 créditos) y **4 de 8** con 4,0 (12 créditos).
- **Qué decir:** «Se puede usar para becas o traslados: se compara el rendimiento sin pedir documentos».

### Escenas de apoyo

#### Escena 14. Qué es una API (opcional, 30 segundos)
- **Clics:** en cualquier consulta exitosa, abre *Ver respuesta JSON*.
- **Qué decir:** «Esto es lo que recibe cualquier programa de otra universidad: texto estructurado. La pantalla solo lo presenta bonito».

#### Escena 15. Servidor apagado (NO hacerla en vivo)
Apagar el servidor (`Ctrl+C`) y consultar muestra «Sin conexión: no se pudo conectar con el servidor». Es útil para probar en privado, pero **no la hagas delante del público**: tendrías que volver a encender la demo.

### 6.3 Resumen: qué se rechaza y por qué

| Escena | Clics clave | Resultado | Control que falla |
|---|---|---|---|
| 2. Sin token | Sin token | 403 | 1. Token presente |
| 3. Token expirado | Token expirado | 403 | 2. Firma y vigencia |
| 4. Token alterado | Borrar una letra del token | 403 | 2. Firma y vigencia |
| 5. Texto que no es token | Escribir texto cualquiera | 403 | 2. Firma y vigencia |
| 6. Token de otra persona | Generar token de Laura y consultar a Valentina | 403 | 3. Titular |
| 7. No existe | Código `12345` y Token válido | 404 | 4. Búsqueda |
| 8. Código mal escrito | `abc def` | Mensaje en pantalla, no se envía | (antes de enviar) |
| 1. Todo bien | Token válido | 200 | Ninguno |

---

## 7. Guion de la exposición (12 a 14 minutos)

Los bloques marcados *(opcional)* se pueden omitir: sin ellos la exposición dura unos 10 minutos.

**Lista de verificación 10 minutos antes:**
- [ ] Plan A: la demo corriendo y la pantalla abierta en `http://127.0.0.1:8000` (sección 3).
- [ ] Plan B: la URL de AWS abierta en **otra pestaña**, con una consulta de prueba hecha para calentar la Lambda (sección 4, paso 10).
- [ ] Las escenas 1, 2 y 3 probadas una vez en cada plan.
- [ ] La terminal de la demo abierta y sin cerrar.
- [ ] Presentación con el esquema de la sección 2 lista.

| Minutos | Bloque | Qué haces | Qué dices |
|---|---|---|---|
| 0:00 a 1:30 | **1. Apertura** | Diapositiva de inicio o la pantalla de la demo. | Las universidades guardan los historiales cada una por su lado. Una homologación puede tardar de 15 a 45 días hábiles por trámites en papel. RFHA-IES conecta las universidades **sin juntar los datos**. |
| 1:30 a 3:00 | **2. Qué es el middleware** | Muestra el esquema de la sección 2. | El middleware es un intermediario con tres funciones: **transportista** (una sola dirección), **seguridad** (revisa el permiso antes de tocar los datos) y **traductor** (entrega siempre el mismo formato). |
| 3:00 a 4:30 | **3. Caso exitoso** | Escena 1 (Brayan). | Explica los cuatro controles en verde, el expediente, los créditos. |
| 4:30 a 6:00 | **4. Rechazos** | Escenas 2, 3 y 4. | Tres intentos fallidos, tres controles distintos. «Sin permiso no hay acceso». |
| 6:00 a 7:00 | **5. Privacidad** | Escena 6 (Laura y Valentina). | El permiso es personal. |
| 7:00 a 8:30 | **6. Red federada** | Escena 9 (tres universidades). | Una pantalla, tres universidades. Transparencia de acceso y de ubicación. |
| 8:30 a 10:00 | **7. Homologación** | Escena 10 (Laura). | El caso de uso real: pasar de semanas a segundos. |
| 10:00 a 10:45 | **8. Más estados** *(opcional)* | Escenas 11 y 12 (Andrés, Juan). | El mismo servicio atiende graduados, activos y retirados. |
| 10:45 a 11:15 | **9. No existe** *(opcional)* | Escena 7 (`12345`). | Diferencia entre «sin permiso» (403) y «no existe» (404). |
| 11:15 a 12:15 | **10. Mismo código en AWS** | Cambia a la pestaña de AWS y repite la escena 1. | Es el mismo programa corriendo en la nube de Amazon, sin servidores. Cambió la dirección, no el comportamiento. |
| 12:15 a 13:15 | **11. Avance del proyecto final** *(opcional)* | En otra terminal: `.\run-app.cmd`, abre `http://127.0.0.1:8001/registro-nodo` y registra una universidad. | La historia HU-01 ya está terminada: una universidad solicita unirse y queda «pendiente de aprobación». |
| 13:15 a 14:00 | **12. Cierre** | Diapositiva final. | Se demostró seguridad por consentimiento y transparencia de acceso y de ubicación sobre una arquitectura serverless. Falta: copia de respaldo ante caídas, bitácora de consultas y portal del estudiante. |

---

## 8. Por qué cumple con la exposición y con la propuesta

### 8.1 Exposición de Middleware y Web Services

| Lo que pide la exposición | Cómo lo cumple la demo | Dónde se ve |
|---|---|---|
| **Middleware:** intermediario que da «visión de sistema único» y oculta la complejidad | El usuario usa una sola pantalla y una sola dirección; no sabe en qué servidor ni base de datos está cada dato. | Escena 9. |
| **Transportista:** recibe la petición y la encamina | API Gateway recibe y entrega a la Lambda, que decide la respuesta. | Plan B. |
| **Seguridad en la capa intermedia** | Se valida el permiso **antes** de tocar los datos. | Escenas 2 a 6. |
| **Ocultar la diferencia entre sistemas** | Siempre se responde con el mismo formato (JSON), de cualquier universidad. | Escenas 9 y 14. |
| **Web service** con estándares abiertos | API REST sobre HTTP, con JSON y códigos 200, 403 y 404. | La insignia HTTP y el JSON. |
| **Contrato documentado** | La documentación se genera sola en `/docs`. | Pie de la pantalla. |
| **Interoperabilidad** | Cualquier programa que hable HTTP puede usarlo, no solo esta pantalla. | Apéndice, sección 12. |

**Transparencias de Sistemas Distribuidos que se pueden mostrar:** *de acceso* (misma forma de consultar), *de ubicación* (no se sabe dónde están los datos) y, solo explicada, *de escalado* (Lambda crea más copias si hay más peticiones).

### 8.2 Cumplimiento de la propuesta del proyecto

La demo es un recorte funcional de la propuesta: **consultar un historial solo con el consentimiento del estudiante**.

| Requisito de la propuesta | Estado en la demo |
|---|---|
| **HU-06** Consulta federada con token | **Cumplido en versión mínima.** |
| **HU-07** Bloqueo de consultas sin permiso | **Cumplido.** Sin token, vencido, alterado o de otra persona dan 403. |
| **RF-05** Consulta transparente por el middleware | **Cumplido (mínimo).** |
| **RF-06** Rechazo por falta o expiración del token (403) | **Cumplido.** |
| **RF-07** Ver el historial para homologar | **Cumplido y ampliado:** materias, créditos, notas, estados y panel de homologación. |
| **Token firmado (JWT)** | **Cumplido.** Firma HS256 y fecha de vencimiento obligatoria. |
| **Arquitectura serverless en AWS (API Gateway + Lambda, Python, FastAPI + Mangum)** | **Cumplido.** |
| **HTTPS** | **Cumplido en AWS** (por defecto). En local es HTTP porque es solo desarrollo. |
| **Costo cero** | **Cumplido.** Sin base de datos, con límite de peticiones y logs de 7 días. |
| **Interfaz web responsiva** | **Cumplido** en la demo (accesible, claro/oscuro, celular). |

**Lo que la demo todavía NO hace** (no lo prometas en la exposición): registro y aprobación de universidades con clave de API (HU-02), carga de historiales en base de datos (HU-03), que el estudiante genere y revoque sus tokens (HU-04 y HU-05), enrutamiento real entre varias bases de datos (HU-06 completa), copia de respaldo ante caídas (HU-08) y bitácora de consultas (HU-09). El registro de universidades (HU-01) ya existe en el proyecto final.

**Frase de cierre sugerida:** «La demo implementa el corazón de la propuesta: un middleware que solo entrega el historial cuando el estudiante dio su consentimiento firmado. Usa el mismo stack del proyecto final y ya corre en AWS. Los demás módulos se construyen sobre esta base».

---

## 9. Cómo funciona el código

No necesitas leer el código para exponer, pero esto sirve para responder preguntas.

### 9.1 Mapa de archivos

| Archivo | Para qué sirve |
|---|---|
| `demo/main.py` | **El programa principal:** valida el token, busca al estudiante, entrega la respuesta y sirve la pantalla. |
| `demo/students.py` | Los 6 estudiantes ficticios con sus materias. Aquí se editan los datos de prueba. |
| `demo/static/` | La pantalla: `index.html` (estructura), `styles.css` (apariencia) y `app.js` (comportamiento). |
| `demo/template.yaml` | La receta para AWS: crea la Lambda, la puerta de entrada y los registros. |
| `demo/requirements.txt` | Lista de librerías que necesita la Lambda. |
| `demo/requirements-local.txt` | Lo mismo más el servidor local. |
| `scripts/run_demo.py` | El lanzador de un solo comando. |
| `scripts/generate_token.py` y `scripts/check_demo.py` | Respaldo por comandos (apéndice). |
| `demo/tests/` | Pruebas automáticas que GitHub ejecuta en cada subida de código. |

### 9.2 `demo/main.py` por partes

1. **Configuración.** Lee el secreto (`JWT_SECRET`) y si el modo demostración está activo (`DEMO_MODE`). En AWS llegan como variables de entorno; en el computador, de un archivo `.env`.
2. **Datos.** Importa los 6 estudiantes de `students.py` y los guarda en memoria. Representan lo que cada universidad guardaría en su propia base de datos.
3. **La validación del token** (`verify_student_token`). Son los tres controles de seguridad, en este orden:
   - Si no hay token, rechaza con 403.
   - Si la firma es mala o el token venció, rechaza con 403. La librería PyJWT hace la revisión; se exige que el token traiga fecha de vencimiento.
   - Si el estudiante que dice el token no es el consultado, rechaza con 403.
4. **El servicio principal.** `GET /api/v1/federated/academic-history/{código}`: primero valida, **después** busca. Si el estudiante no existe, responde 404. Si todo está bien, 200 con el historial.
   *Detalle técnico:* el encabezado del token se declara opcional a propósito. Si fuera obligatorio, el framework respondería 422 cuando falta, y lo correcto en seguridad es 403.
5. **Ayudas de la demo** (solo si `DEMO_MODE=1`): una para listar estudiantes de ejemplo y otra para fabricar tokens de prueba. Si está apagado, responden 404.
6. **La pantalla.** Entrega `index.html` en la dirección raíz y los archivos de `static/`, con cabeceras de seguridad que impiden ejecutar código no autorizado.
7. **`handler = Mangum(app)`.** Es el adaptador para AWS: API Gateway habla en un formato propio y Mangum lo traduce al que entiende el programa. El resto del código es idéntico en local y en AWS.

### 9.3 La pantalla (`demo/static/`)
- Está hecha con HTML, CSS y JavaScript puros, sin librerías externas: carga rápido y es más segura.
- Los textos que vienen del servidor se insertan siempre como texto, nunca como código, para evitar ataques.
- Es accesible: se puede usar con teclado, funciona con lector de pantalla, tiene buen contraste, se adapta al celular y cambia a modo oscuro según el sistema.

### 9.4 `demo/template.yaml` (la receta de AWS)

| Elemento | Qué hace |
|---|---|
| `JwtSecret` | Recibe el secreto al desplegar. No se muestra en pantalla. Mínimo 32 caracteres. |
| `DemoMode` | `0` o `1`: apaga o enciende los botones de simulación (sección 4.1). |
| `DemoApi` | La puerta de entrada pública. Límite de 20 peticiones por segundo para evitar abusos. |
| `DemoFunction` | La Lambda `rfha-demo`: Python 3.11, 256 MB, 10 segundos máximo. |
| `DemoLogGroup` | Registro de actividad que se borra a los 7 días (evita costos ocultos). |
| `ApiUrl` | Imprime la dirección pública al terminar. |

---

## 10. Preguntas probables de los docentes

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué un token JWT? | Va firmado: si alguien lo altera se rechaza (escena 4), lleva fecha de vencimiento y no hace falta consultar una base de datos para validarlo. |
| ¿Quién genera el token? | En la demo, los botones de simulación. En el proyecto final lo genera el propio estudiante (HU-04) y puede revocarlo (HU-05). |
| ¿Dónde está el secreto? | En una variable de entorno de la Lambda, nunca en el código ni en GitHub. |
| ¿Qué pasa si una universidad se cae? | Está previsto un respaldo en una réplica con el encabezado `X-Data-Source` (HU-08). Todavía no está construido. |
| ¿Se registra quién consultó? | Está previsto en una bitácora que solo permite agregar (HU-09). Todavía no está construida. |
| ¿Por qué serverless? | No hay servidores que administrar, escala sola y entra en la capa gratuita. |
| ¿Son datos reales? | No. Los 6 estudiantes y sus notas son inventados. |
| ¿Dónde está la base de datos? | En la demo los datos están en memoria. En el proyecto final cada universidad tendrá su tabla en DynamoDB. |
| ¿Cómo se relaciona con Teoría General de Sistemas? | Es un sistema abierto: entradas (petición y token), proceso (los cuatro controles), salidas (expediente) y retroalimentación (rechazos). La sinergia es que la red vale más que cada universidad por separado. |
| ¿Qué es la homologación? | Que una universidad reconozca las materias que el estudiante aprobó en otra. Hoy es lento y en papel. |

---

## 11. Si algo falla en vivo

Regla general: **cambia de plan sin disculparte ni perder tiempo** (de local a AWS o al revés), y retoma desde la escena donde ibas.

| Qué ves | Qué significa | Qué hacer |
|---|---|---|
| La página no carga en local | La demo está apagada o la terminal se cerró. | Cambia a la pestaña de AWS (Plan B). Después, vuelve a ejecutar `.\run-demo.cmd`. |
| La página de AWS no carga o da error | Puede ser internet o la Lambda. | Cambia a la pestaña local (Plan A). |
| La primera consulta en AWS tarda unos segundos | Arranque en frío. | Es normal; espera. Para evitarlo, calienta antes de exponer. |
| Salió 403 con un token que debía servir | Pulsaste **Token válido** y después cambiaste el código, o el token venció. | Pulsa **Token válido** otra vez con el código correcto ya escrito. |
| En AWS no aparecen los botones ni la lista | Se desplegó con `DemoMode=0`. | Usa el Plan A para las pruebas con clics, o pide al compañero redesplegar con `DemoMode=1`. |
| Los botones no hacen nada | La página quedó vieja en el navegador. | Recarga con `Ctrl+F5`. |
| «Sin conexión» al consultar | La demo se apagó. | Vuelve a ejecutar `.\run-demo.cmd`. |
| Una cifra de homologación no coincide con esta guía | Cambió el valor de la nota mínima. | Ajusta la nota mínima al valor de la escena (3,5 por defecto). |
| Sin internet | Imposible usar AWS. | Usa solo el Plan A. |

---

## 12. Apéndice: respaldo con comandos

Solo para cuando la pantalla no esté disponible. **No se usa en la exposición.**

**Generar tokens** (con el mismo secreto de la demo):
```powershell
python scripts/generate_token.py                # token válido y token expirado de Brayan
python scripts/generate_token.py 20251234501    # tokens de otro estudiante (por ejemplo, Laura)
```

**Probar una dirección** (local o AWS) y verificar los tres escenarios básicos:
```powershell
python scripts/check_demo.py http://127.0.0.1:8000
python scripts/check_demo.py https://abc123xyz.execute-api.us-east-1.amazonaws.com
```
Debe terminar con `TODO BIEN`. Para AWS, antes: `py -3.11 -m pip install PyJWT` y `$env:JWT_SECRET = "<el secreto>"`.

**Una consulta suelta** (en PowerShell se usa `curl.exe`):
```powershell
curl.exe -i -H "X-Student-Consent-Token: <TOKEN>" http://127.0.0.1:8000/api/v1/federated/academic-history/20262678029
```
Sin el encabezado `-H ...` la respuesta es 403.

**Documentación interactiva de la API:** `http://127.0.0.1:8000/docs` (se puede probar el servicio desde ahí).

**Pruebas automáticas:** las ejecuta GitHub en cada subida de código. Localmente: `pytest`.
