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
7. [Lista de verificación antes de exponer](#7-lista-de-verificación-antes-de-exponer)
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

Todos se hacen **con clics, delante del público**. Cada escena indica: qué clics dar, qué se ve y **cómo se refleja el middleware** (qué revisa y qué decide por dentro). Antes de las escenas, la sección 6.2 explica el recorrido de una consulta, que es común a todas.

### 6.1 Los 6 estudiantes de la demo (datos ficticios)

| Código | Estudiante | Universidad | Programa | Estado | Promedio | Créditos | Sirve para |
|---|---|---|---|---|---|---|---|
| `20262678029` | **Brayan Acosta Parrado** | Distrital | Ingeniería en Telemática | Activo | 4,52 | 140 de 160 | Caso principal, rechazos y AWS. 8 materias, una en curso. |
| `20251234501` | **Laura Camila Ríos Herrera** | Nacional | Ingeniería de Sistemas y Computación | Activo | 4,18 | 118 de 160 | **Homologación**: reprobó Cálculo Integral (2,6) y lo repitió (3,4). |
| `20241122002` | **Andrés Felipe Moreno Castro** | Javeriana | Ingeniería Electrónica | **Graduado** | 4,05 | 168 de 168 | Título y fecha de grado. |
| `20231098763` | **Valentina Torres Quintero** | Andes | Economía | Activo | 4,62 | 90 de 140 | Promedio alto. |
| `20221050914` | **Juan Sebastián Pardo Gil** | Distrital | Ingeniería Industrial | **Retirado** | 3,21 | 64 de 160 | Promedio bajo y materias repetidas. |
| `20252345678` | **María Fernanda Ospina Duarte** | Nacional | Estadística | Activo | 3,88 | 52 de 150 | Primeros semestres. |

### 6.2 Cómo viaja una consulta (vale para todas las escenas)

Cada vez que pulsas **Consultar expediente** pasa lo mismo, y es lo que explican las escenas de abajo:

```
Pantalla ──(1)──▶ API Gateway ──(2)──▶ Lambda con el MIDDLEWARE ──(3)──▶ Datos ──(4)──▶ Respuesta
 (navegador)       (puerta de AWS)      revisa los 4 controles           (solo si pasan)   200, 403 o 404
```

1. **La pantalla envía una petición** (un `GET`) a una sola dirección. El código del estudiante va dentro de la dirección y el token va en un encabezado llamado `X-Student-Consent-Token`.
2. **La recibe el servicio.** En AWS la recibe API Gateway y se la pasa a la Lambda; en tu computador la recibe el servidor local. **El programa es el mismo.**
3. **El middleware revisa cuatro controles, en orden, y se detiene en el primero que falla.**
4. **Solo si pasan los tres primeros controles se toca el dato.** Después responde con un código (200, 403 o 404) y un texto en JSON. La pantalla pinta los controles según esa respuesta.

| Control | Cómo lo revisa el middleware | Si falla, responde |
|---|---|---|
| **1. Token presente** | Mira si llegó el encabezado con el token. | `403`: «falta el token de consentimiento» |
| **2. Firma y vigencia** | Abre el token con el secreto compartido: comprueba que la firma coincida (no alterado) y que la fecha de vencimiento no haya pasado. Exige que el token traiga fecha de vencimiento. | `403`: «ha expirado» o «inválido» |
| **3. Titular del consentimiento** | Compara el estudiante que está escrito **dentro** del token con el estudiante de la dirección. | `403`: «el token no autoriza a este estudiante» |
| **4. Búsqueda del expediente** | Busca el código en los datos de la red. | `404`: «estudiante no encontrado» |
| *Todo bien* | Entrega el expediente. | `200` con `status: SUCCESS`, `middleware_layer`, `transparency_verified: true` y `data` |

> **Detalle técnico:** la respuesta de error solo trae el mensaje. La pantalla deduce qué control falló leyendo ese mensaje y por eso puede iluminarlo.
> **Idea clave:** el middleware **no guarda memoria** de consultas anteriores (es *sin estado*). Cada petición se revisa desde cero, y eso le permite crecer en AWS sin cambiar nada.

### 6.3 Antes de empezar cada escena
Recarga la página (`F5`) para dejar todo limpio, salvo que la escena diga lo contrario.

### Escenas de seguridad (los rechazos)

#### Escena 1. Consulta exitosa
- **Objetivo:** mostrar el camino feliz.
- **Clics:**
  1. En *Estudiante de ejemplo* elige **Brayan Acosta Parrado**.
  2. Pulsa **Token válido**. El campo del token se llena.
  3. Pulsa **Consultar expediente**.
- **Qué se ve:** los 4 controles en **verde**, insignia **HTTP 200**, mensaje «Acceso concedido: el estudiante autorizó la consulta». Aparece Brayan (Activo), promedio 4,52, «140 de 160 (88 %)» y 8 materias; la última, «En curso». Abre *Ver respuesta JSON* para ver lo que viajó por la red.
- **Cómo se refleja el middleware:**
  - **Petición:** llega el código `20262678029` y un token firmado para ese mismo estudiante, vigente por 24 horas.
  - **Control 1:** el token llegó. **Control 2:** la firma coincide con el secreto y no está vencido. **Control 3:** el token dice «20262678029» y la dirección dice «20262678029»: coinciden. **Control 4:** el estudiante existe.
  - **Decisión:** abre la puerta y entrega el expediente. **Respuesta:** `200` con el historial en JSON y la marca `transparency_verified: true`.
- **Conclusión:** el expediente solo sale después de superar los cuatro controles. Es el comportamiento base que las demás escenas ponen a prueba.

#### Escena 2. Sin token
- **Clics:** Brayan elegido, pulsa **Sin token** (el campo del token queda vacío) y **Consultar expediente**.
- **Qué se ve:** **HTTP 403**, mensaje «ACCESO DENEGADO: falta el token de consentimiento del estudiante». Control 1 en **rojo** y controles 2, 3 y 4 en «Omitido». **No aparece ningún dato.**
- **Cómo se refleja el middleware:**
  - **Petición:** llega el código, pero **sin** el encabezado del token.
  - **Control 1** falla de inmediato. El middleware **ni siquiera abre el token ni busca al estudiante**: corta ahí.
  - **Respuesta:** `403`. Los controles 2, 3 y 4 quedan «Omitido» porque nunca se ejecutaron.
- **Conclusión:** sin permiso no hay acceso, y el dato nunca se consulta. Por eso no hay riesgo de filtrar información por accidente.
- *Nota técnica:* el sistema responde `403` y no `422` (el error que daría el framework por defecto cuando falta un encabezado obligatorio), porque aquí lo correcto es negar el acceso.

#### Escena 3. Token expirado
- **Clics:** Brayan elegido, pulsa **Token expirado** y **Consultar expediente**.
- **Qué se ve:** **HTTP 403**, «El token de consentimiento ha expirado». Control 1 verde, control 2 **rojo**, controles 3 y 4 «Omitido».
- **Cómo se refleja el middleware:**
  - **Petición:** el token **sí llegó** y **sí es auténtico** (fue firmado con el secreto correcto), pero su fecha de vencimiento ya pasó.
  - **Control 1** pasa. **Control 2** abre el token, ve que la fecha venció y lo rechaza con el mensaje específico «ha expirado».
  - **Respuesta:** `403`. No se revisa el titular ni se busca al estudiante.
- **Conclusión:** el consentimiento es **temporal**. Un permiso viejo deja de servir solo, sin que nadie tenga que anularlo.

#### Escena 4. Token alterado
- **Clics:** Brayan elegido, pulsa **Token válido**. Haz clic dentro del recuadro del token y borra **una letra del final** (tecla Retroceso). Pulsa **Consultar expediente**.
- **Qué se ve:** **HTTP 403**, «ACCESO DENEGADO: token de consentimiento inválido». Control 1 verde, control 2 **rojo**.
- **Cómo se refleja el middleware:**
  - **Petición:** llega un token al que le falta una letra.
  - **Control 2:** la firma del token se calculó con el secreto sobre el contenido original. El middleware vuelve a calcularla y **ya no coincide**, así que el token se declara inválido.
  - **Respuesta:** `403`.
- **Conclusión:** cambiar una sola letra rompe la firma. Quien no conoce el secreto **no puede fabricar ni modificar** un token que el sistema acepte.

#### Escena 5. Texto que no es un token
- **Clics:** Brayan elegido. En el recuadro del token escribe `esto-no-es-un-token` y pulsa **Consultar expediente**.
- **Qué se ve:** **HTTP 403**, «token de consentimiento inválido». Control 2 rojo.
- **Cómo se refleja el middleware:**
  - **Petición:** llega un texto cualquiera en el encabezado del token.
  - **Control 1:** hay algo escrito, así que pasa. **Control 2:** un token real tiene tres partes separadas por puntos y una firma; este texto no tiene esa estructura, así que **ni siquiera se puede abrir**.
  - **Respuesta:** `403`.
- **Conclusión:** inventar un token no sirve. El middleware no confía en lo que le envían: lo verifica.

#### Escena 6. El token es de una persona
- **Objetivo:** mostrar la privacidad entre estudiantes.
- **Clics:**
  1. Elige **Laura Camila Ríos Herrera**.
  2. Pulsa **Token válido** (es el permiso de Laura).
  3. **Sin tocar el token**, elige ahora **Valentina Torres Quintero** en la lista.
  4. Pulsa **Consultar expediente**.
- **Qué se ve:** **HTTP 403**, «ACCESO DENEGADO: el token no autoriza a este estudiante». Controles 1 y 2 verdes, control 3 **rojo**.
- **Cómo se refleja el middleware:**
  - **Petición:** la dirección pide a Valentina (`20231098763`), pero el token fue firmado para Laura (`20251234501`).
  - **Controles 1 y 2** pasan: el token es auténtico y está vigente.
  - **Control 3:** compara el estudiante escrito dentro del token con el de la dirección. **No coinciden**, así que lo rechaza.
  - **Respuesta:** `403`. El expediente de Valentina no se toca.
- **Conclusión:** un token auténtico y vigente **no basta**: debe ser del titular de los datos. Cada estudiante decide quién ve su información.

#### Escena 7. Estudiante que no existe
- **Clics:**
  1. En *Código del estudiante* escribe `12345` (no uses la lista).
  2. Pulsa **Token válido** (se firma para `12345`).
  3. Pulsa **Consultar expediente**.
- **Qué se ve:** **HTTP 404**, «Estudiante no encontrado en la red federada». Controles 1, 2 y 3 **verdes**, control 4 **rojo**.
- **Cómo se refleja el middleware:**
  - **Petición:** el token es válido, vigente y fue firmado para `12345`, el mismo código que pide la dirección.
  - **Controles 1, 2 y 3** pasan. **Control 4:** el middleware busca `12345` en los datos de la red y **no lo encuentra**.
  - **Respuesta:** `404`.
- **Conclusión:** el middleware distingue «no tienes permiso» (**403**) de «eso no existe» (**404**). La búsqueda ocurre **después** de validar el permiso: quien no tiene token recibe siempre 403, exista o no el estudiante, así que no puede averiguar quién está en la red.

#### Escena 8. Código mal escrito
- **Clics:** en *Código del estudiante* escribe `abc def` (con espacio) y pulsa **Consultar expediente**. Prueba también con el campo vacío.
- **Qué se ve:** un mensaje rojo bajo el campo: «Escribe un código válido: solo letras, números, guion o guion bajo (máximo 32)». **El panel de validación no cambia: no se envió nada.**
- **Cómo se refleja el middleware:**
  - **Aquí el middleware no interviene:** la pantalla detiene el envío antes de que la petición salga. Es una **primera capa** que mejora la experiencia de quien escribe.
  - **El servidor no depende de ella:** todo lo que sí llega al middleware pasa igual por los cuatro controles. La validación de la pantalla ayuda; la que protege es la del middleware.
- **Conclusión:** conviene validar en dos lugares: en la pantalla para avisar rápido y en el middleware para no confiar en nadie.

### Escenas de la red federada y la homologación

#### Escena 9. Tres universidades, una sola pantalla
- **Objetivo:** transparencia de acceso y de ubicación.
- **Clics:** repite los pasos de la escena 1 (elegir, **Token válido**, **Consultar expediente**) con **Laura** (Nacional), **Andrés Moreno** (Javeriana) y **Valentina Torres** (Andes). No hace falta recargar entre una y otra.
- **Qué se ve:** cada vez cambia «Universidad de origen», pero el formato, los cuatro controles y la forma de consultar son idénticos.
- **Cómo se refleja el middleware:**
  - Las tres consultas usan **la misma dirección, el mismo programa y los mismos cuatro controles**. El middleware no tiene reglas distintas por universidad.
  - **Entrega los tres expedientes con los mismos campos** (nombre, universidad, programa, promedio, créditos y lista de materias con código, nombre, créditos, nota, estado y semestre). Así se **oculta la diferencia entre universidades**.
  - *Honestidad técnica:* en la demo los datos de las cuatro universidades están juntos en la memoria del programa. En el proyecto final, el middleware consultará un catálogo de nodos para saber en qué base de datos de cada universidad está el estudiante, **sin cambiar nada de lo que ves**.
- **Conclusión:** **transparencia de acceso** (se consulta igual) y **de ubicación** (no se sabe dónde viven los datos).

#### Escena 10. Homologación con Laura
- **Objetivo:** el uso real: decidir qué materias reconocer.
- **Clics:** consulta a **Laura** (como en la escena 1). Baja a *Apoyo a la homologación*. Con **3,5** en *Nota mínima aceptada* lee la frase. Cambia el valor a **4,0** y vuelve a leerla.
- **Qué se ve:**
  - Con 3,5: «**8 de 9** asignaturas aprobadas tienen nota de 3,5 o más: **25 créditos** candidatos a homologar». Las filas candidatas se pintan en verde y dicen «candidata».
  - Con 4,0: «**7 de 9** … **21 créditos**». Queda fuera Física Mecánica (3,9).
  - Cálculo Integral aparece dos veces: 2024-2 en rojo «Reprobada» (2,6) y 2025-1 «Aprobada» (3,4), que **no** es candidata con 3,5.
  - La materia de 2026-2 dice «En curso» y no cuenta.
- **Cómo se refleja el middleware:**
  - **El cálculo lo hace la pantalla**, no el middleware: al mover la nota mínima, la pantalla recorre la lista de materias que ya recibió. No se hace una nueva consulta.
  - **El aporte del middleware es la información normalizada:** cada materia llega con los mismos campos (créditos, nota, estado, semestre) sin importar de qué universidad venga. Si cada universidad enviara un formato distinto, no se podrían comparar ni sumar.
  - Para llegar hasta aquí la consulta ya superó los cuatro controles de la escena 1.
- **Conclusión:** cada universidad que recibe fija su criterio y decide en segundos. El middleware hace posible la comparación porque entrega datos uniformes **y solo con el permiso del estudiante**.

#### Escena 11. Un graduado (Andrés)
- **Clics:** elige **Andrés Felipe Moreno Castro**, **Token válido**, **Consultar expediente**.
- **Qué se ve:** estado **Graduado**; aparecen *Título* («Ingeniero Electrónico») y *Fecha de grado* («2025-12-12»). Créditos «168 de 168 (100 %)». Con nota mínima 3,5: 6 de 6 (20 créditos); con 4,0: 5 de 6 (16 créditos).
- **Cómo se refleja el middleware:**
  - **Mismos cuatro controles** que en la escena 1; todos verdes.
  - **Cambia el contenido, no el trato:** el registro de Andrés tiene dos datos más (título y fecha de grado) y el middleware los entrega tal cual. La pantalla muestra esos campos solo cuando existen.
  - Esto es posible porque los datos se guardan sin un esquema rígido (tipo documento), así que cada registro puede traer campos distintos.
- **Conclusión:** el mismo servicio atiende egresados y estudiantes activos, y sirve para verificar un título sin pedir un certificado en papel.

#### Escena 12. Un retirado (Juan)
- **Clics:** elige **Juan Sebastián Pardo Gil**, **Token válido**, **Consultar expediente**.
- **Qué se ve:** estado **Retirado** (en rojo), promedio 3,21, «64 de 160 (40 %)». Dos materias reprobadas: Física I (2,8) y Probabilidad (2,9); Física I aparece repetida y aprobada (3,4). Con nota mínima 3,5: **2 de 6** candidatas (Química General y Dibujo Técnico, **5 créditos**).
- **Cómo se refleja el middleware:**
  - **Mismos cuatro controles**, todos verdes: el estudiante dio su permiso.
  - **El middleware no juzga el estado académico:** mientras exista el consentimiento, entrega el expediente completo y con honestidad (materias reprobadas incluidas). Qué hacer con esa información lo decide la universidad que consulta.
  - *Nota:* en el proyecto final se podrán agregar reglas de negocio por estado; la demo no las tiene.
- **Conclusión:** un estudiante que se va y quiere continuar en otra universidad puede mostrar su historial real, y el sistema deja ver con claridad qué se le puede reconocer.

#### Escena 13. Promedio alto y primeros semestres
- **Clics:** consulta a **Valentina** (promedio 4,62) y luego a **María Ospina** (52 de 150 créditos, 35 %). Para cada una: elegirla, **Token válido**, **Consultar expediente**.
- **Qué se ve:** con nota mínima 4,5, Valentina tiene **7 de 8** candidatas (22 créditos; Econometría I con 4,4 queda fuera). María tiene **8 de 8** con 3,5 (26 créditos) y **4 de 8** con 4,0 (12 créditos).
- **Cómo se refleja el middleware:**
  - **Son dos consultas independientes.** Cada una necesita su propio token. Si usaras el token de Valentina para consultar a María, volverías a la escena 6.
  - El middleware **no recuerda** la consulta anterior (es *sin estado*): revisa de nuevo los cuatro controles. Gracias a eso, miles de consultas simultáneas se pueden atender sin que se mezclen.
- **Conclusión:** se puede usar para becas o traslados comparando el rendimiento sin pedir documentos, y cada consulta queda protegida por separado.

### Escenas de apoyo

#### Escena 14. Qué es una API y «Copiar como curl»
- **Clics:** en cualquier consulta exitosa, abre *Ver respuesta JSON*. Después pulsa **Copiar como curl** y pega el texto en cualquier lugar (por ejemplo, el bloc de notas).
- **Qué se ve:** un texto estructurado con cuatro campos: `status`, `middleware_layer`, `transparency_verified` y `data`. Con el botón se copia un comando como `curl -i -H "X-Student-Consent-Token: ..." "http://127.0.0.1:8000/api/v1/federated/academic-history/20262678029"`.
- **Cómo se refleja el middleware:**
  - **Ese JSON es la respuesta real del middleware.** La pantalla solo lo presenta bonito: cualquier otro programa recibe exactamente el mismo texto.
  - `middleware_layer` indica por dónde pasó la consulta («AWS API Gateway + AWS Lambda») y `transparency_verified: true` marca que se superaron los controles.
  - **Para qué sirve «Copiar como curl»:** `curl` es una herramienta de terminal que hace peticiones web. El botón copia la consulta que acabas de hacer, con su código y su token, para repetirla fuera de la pantalla. Demuestra que el servicio es una **API abierta**, usable por cualquier programa de otra universidad, no solo por esta página. Es opcional.
- **Conclusión:** el middleware expone un servicio estándar (REST con JSON); la pantalla es solo un cliente más.

#### Escena 15. Servidor apagado (NO hacerla en vivo)
- **Qué se ve:** si apagas la demo (`Ctrl+C`) y consultas, la pantalla muestra «Sin conexión» y «No se pudo conectar con el servidor».
- **Cómo se refleja el middleware:** la petición **no llega a ningún middleware**, así que no hay respuesta, ni código 200, 403 ni 404. Eso es diferente de un rechazo: los 403 y 404 **sí** son respuestas del middleware. En el proyecto final, este caso lo cubrirá la copia de respaldo ante caídas (HU-08).
- **Recomendación:** pruébala en privado. **No la hagas delante del público**, porque tendrías que volver a encender la demo.

### 6.4 Resumen: qué se rechaza, por qué y cómo lo resuelve el middleware

| Escena | Clics clave | Resultado | Control que falla | Cómo lo resuelve el middleware |
|---|---|---|---|---|
| 1. Todo bien | Token válido | 200 | Ninguno | Pasa los 4 controles y entrega el expediente. |
| 2. Sin token | Sin token | 403 | 1. Token presente | Corta al ver que no hay token; no toca el dato. |
| 3. Token expirado | Token expirado | 403 | 2. Firma y vigencia | Detecta la fecha vencida del token auténtico. |
| 4. Token alterado | Borrar una letra del token | 403 | 2. Firma y vigencia | La firma recalculada no coincide. |
| 5. Texto que no es token | Escribir texto cualquiera | 403 | 2. Firma y vigencia | No se puede abrir: no tiene estructura de token. |
| 6. Token de otra persona | Generar token de Laura y consultar a Valentina | 403 | 3. Titular | El estudiante del token no es el de la dirección. |
| 7. No existe | Código `12345` y Token válido | 404 | 4. Búsqueda | Permiso válido, pero el estudiante no está en la red. |
| 8. Código mal escrito | `abc def` | Mensaje en pantalla | (antes de enviar) | No interviene: la pantalla frena el envío. |
| 9 a 13. Otras universidades y estados | Elegir, Token válido, Consultar | 200 | Ninguno | Mismos controles y mismo formato para todas. |
| 14. API abierta | Ver JSON / Copiar como curl | — | — | Muestra que la respuesta es un servicio estándar. |

---

## 7. Lista de verificación antes de exponer

Revísala unos 10 minutos antes de empezar.

- [ ] **Plan A:** la demo corriendo en el computador y la pantalla abierta en `http://127.0.0.1:8000` (sección 3). Arriba a la derecha dice **Entorno: Local**.
- [ ] **Plan B:** la URL de AWS abierta en **otra pestaña**, con una consulta de prueba hecha para despertar la Lambda (sección 4, paso 10). Arriba a la derecha dice **Entorno: Nube (AWS)**.
- [ ] Las escenas 1, 2 y 3 probadas una vez en cada plan.
- [ ] La terminal de la demo abierta y sin cerrar.
- [ ] Los botones de **Simular al estudiante** y la lista **Estudiante de ejemplo** visibles (en AWS requieren `DemoMode=1`).
- [ ] El navegador con el zoom adecuado para que se lea desde lejos (`Ctrl` + `+`).
- [ ] La sección 10 (preguntas probables) leída por todos los que van a exponer.

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
