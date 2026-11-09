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
- **Plan B, en AWS.** Queda en internet con una dirección pública. La despliega quien tenga acceso a la cuenta de AWS del equipo.

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

Esta parte la puede hacer **cualquier integrante del equipo** que tenga acceso a la cuenta de AWS. No hace falta saber programar ni abrir otro documento: todo lo necesario está aquí. Sigue los pasos **en orden** y no te saltes las comprobaciones de «Resultado esperado».

### 4.0 Resumen

| | |
|---|---|
| **Qué se crea** | Un paquete llamado **`rfha-demo`** (en AWS se llama *stack*) con: una función **Lambda** (el programa), una **puerta de entrada** pública (API Gateway) y un **registro de actividad** (CloudWatch) que se borra solo a los 7 días. **No usa base de datos.** |
| **Qué se obtiene** | Una dirección pública `https://xxxxxxxx.execute-api.us-east-2.amazonaws.com`. Al abrirla aparece **la misma pantalla** de la demo. |
| **Qué se necesita del equipo** | Un **secreto**: un texto de 32 o más caracteres que firma los tokens (paso 7). |
| **Costo** | USD 0 dentro del Free Tier. |
| **Tiempo** | 45 a 60 minutos la primera vez. Después, 5 minutos. |
| **Reparto sugerido** | La persona que administra la cuenta de AWS hace los pasos 1 a 14. Quien conoce el secreto y el código lo entrega en el paso 7 y revisa las pruebas del paso 12. Pueden ser la misma persona. |

### 4.1 Cómo leer esta guía

- Los nombres de **botones y menús** de AWS aparecen en **negrita** y en inglés, tal como los muestra la consola (la consola de AWS está en inglés por defecto).
- Lo que se escribe en la terminal va en bloques de código y se pega tal cual.
- **AWS cambia el diseño de su consola con frecuencia.** Si un botón no está donde dice la guía, usa la **barra de búsqueda** de la parte superior de la consola y escribe el nombre del servicio (por ejemplo `IAM`, `CloudFormation`, `Billing`). El nombre de las opciones casi nunca cambia.
- **Consola** = el sitio web de AWS en el navegador. **Terminal** = la ventana donde se escriben comandos (PowerShell).
- Cada paso termina con **Resultado esperado** (cómo saber que salió bien) y **Si falla**.

### 4.2 El mapa de lo que vas a hacer

| Fase | Pasos | Dónde | Para qué |
|---|---|---|---|
| **A. Cuenta y seguridad** | 1 a 3 | Consola (navegador) | Tener una cuenta, una alerta de gasto y un usuario con llaves para desplegar. |
| **B. Tu computador** | 4 a 6 | Terminal | Instalar las herramientas y descargar el código. |
| **C. Despliegue** | 7 a 10 | Terminal y navegador | Subir la demo a AWS y abrirla. |
| **D. Comprobación y cierre** | 11 a 14 | Consola y terminal | Entender lo que se creó, probar, y borrar todo al terminar. |

### 4.3 Una decisión importante: el modo demostración

La pantalla tiene unos botones, **Token válido**, **Token expirado** y **Sin token**, que **simulan al estudiante** para poder hacer las pruebas con clics. Esos botones y la lista de estudiantes de ejemplo solo aparecen si la demo se despliega con **`DemoMode=1`**.

| Valor | Qué pasa | Cuándo usarlo |
|---|---|---|
| `DemoMode=1` | Aparecen los botones y la lista. **Cualquiera que conozca la dirección podría generar tokens**, es decir, la protección queda desactivada para quien tenga la URL. | **Para la exposición**, que es temporal. La dirección es larga y aleatoria. **Después de exponer, se borra todo** (paso 14). |
| `DemoMode=0` | No aparecen los botones; solo se puede probar pegando tokens hechos a mano. | Si la demo va a quedar publicada mucho tiempo. |

**Recomendación para la exposición: `DemoMode=1` y borrar el paquete al terminar.** El valor se escribe en el paso 9.

### 4.4 Qué se necesita antes de empezar

- Un computador con **Windows y PowerShell**, con internet.
- Un **correo** que puedas abrir (AWS envía un código de verificación).
- Un **teléfono** que pueda recibir un SMS o una llamada (verificación de identidad).
- Una **tarjeta de crédito o débito** con pagos internacionales. AWS la pide para crear la cuenta aunque no cobre.
- Permiso para instalar programas en el computador.

### 4.5 Paso a paso

---

#### Paso 1. Crear o verificar la cuenta de AWS

*Una cuenta de AWS es el «usuario principal» donde viven todos los servicios y se factura el consumo. Su correo y contraseña forman el **usuario raíz** (root), que es el más poderoso: se usa solo para crear la cuenta, nunca para trabajar a diario.*

**Si el equipo ya tiene cuenta:** salta a 1.5 y verifica el plan.

**1.1 Abrir el sitio.** En el navegador entra a https://aws.amazon.com y pulsa **Create an AWS Account** (arriba a la derecha).

**1.2 Datos de acceso.** Completa el formulario:
- **Root user email address**: un correo tuyo.
- **AWS account name**: un nombre para reconocerla, por ejemplo `rfha-ies`.
- Pulsa **Verify email address**. Revisa tu correo, copia el código de 6 dígitos y pégalo en **Verification code**. Pulsa **Verify**.
- Escribe una contraseña dos veces (**Root user password** y **Confirm root user password**) y pulsa **Continue**.

**1.3 Datos de contacto.** Elige **Personal** como tipo de cuenta (es para un proyecto académico) y completa nombre, teléfono, país y dirección. Pulsa **Continue**.

**1.4 Facturación e identidad.** Escribe los datos de la tarjeta y pulsa **Verify and continue**. Luego AWS verifica tu teléfono: elige **Text message (SMS)** o **Voice call**, escribe el número, resuelve el código de seguridad (captcha) y escribe el código de 4 dígitos que recibas. Cuando pregunte por el plan de soporte elige **Basic support - Free**.

> **Importante, el plan de la cuenta.** Las cuentas nuevas pueden elegir entre un plan gratuito (**Free**, con créditos y hasta 6 meses) y un plan de pago (**Paid**). **Elige el plan Free.** Con él no se cobra nada mientras dure el plan; cuando termina (por tiempo o por créditos), no se cobra a menos que decidas pasar a un plan de pago.

**1.5 Entrar a la consola y verificar el plan.**
1. Entra a https://console.aws.amazon.com. Elige **Root user**, escribe el correo y la contraseña.
2. En la barra de búsqueda de arriba escribe `Billing and Cost Management` y entra a ese servicio.
3. En el menú izquierdo busca **Free Tier** (o **Credits**). Debe mostrar el plan activo y el saldo de créditos.

**1.6 Elegir la región.** En la esquina superior derecha de la consola hay un selector con un nombre de región (por ejemplo «Ohio»). Ábrelo y elige **US East (Ohio) us-east-2**. *(Una región es la ubicación geográfica de los servidores. Toda la guía usa esta región.)*

- **Resultado esperado:** ves el panel de **Free Tier** y arriba a la derecha dice **Ohio**.
- **Si falla:** si rechazan la tarjeta, prueba otra con pagos internacionales activados. Si no llega el correo o el SMS, espera unos minutos y usa **Resend**.

---

#### Paso 2. Alerta de gasto de USD 0.01

*Es una red de seguridad: AWS te escribe un correo si se genera aunque sea un centavo de gasto.*

1. En la barra de búsqueda escribe `Billing and Cost Management` y entra.
2. En el menú izquierdo abre **Budgets**.
3. Pulsa **Create budget** (botón naranja).
4. En **Budget setup** elige **Use a template (simplified)**.
5. En la lista de **Templates** elige **Zero spend budget**.
6. En **Budget name** puedes dejar «My Zero-Spend Budget».
7. En **Email recipients** escribe los correos del equipo que quieran recibir el aviso, separados por comas.
8. Pulsa **Create budget** (abajo).

- **Resultado esperado:** vuelves a la lista de **Budgets** y aparece «My Zero-Spend Budget» con el gasto actual en 0.
- **Si falla:** si no aparece la plantilla, elige **Customized (advanced)**, luego **Cost budget** y **Next**. En **Period** elige **Monthly**, en **Budget amount** escribe `0.01`, pulsa **Next**, agrega una alerta (**Add an alert threshold**) con **Threshold** `100` % de **Actual** y tu correo en **Email recipients**, y pulsa **Create budget**.

---

#### Paso 3. Crear un usuario para desplegar

*IAM es el servicio de usuarios y permisos de AWS. Se crea un usuario solo para esta tarea, con permisos limitados, en lugar de usar el usuario raíz, que es más peligroso. Una **política** es un permiso con nombre.*

**3.1 Crear el usuario.**
1. En la barra de búsqueda escribe `IAM` y entra.
2. En el menú izquierdo abre **Users**.
3. Pulsa **Create user**.
4. En **User name** escribe `rfha-deployer`.
5. **Deja sin marcar** la casilla «Provide user access to the AWS Management Console» (este usuario solo se usará desde la terminal).
6. Pulsa **Next**.

**3.2 Darle permisos.**
1. En **Permissions options** elige **Attach policies directly**.
2. Aparece una lista larga llamada **Permissions policies** con un cuadro de búsqueda. Escribe el nombre de cada política, **marca la casilla** de la fila exacta y sigue con la siguiente. Debes marcar estas **6**:

   | Política (escríbela en el buscador) | Para qué la necesita |
   |---|---|
   | `AWSCloudFormationFullAccess` | Crear y borrar el paquete (*stack*). |
   | `AWSLambda_FullAccess` | Crear la función Lambda. |
   | `AmazonAPIGatewayAdministrator` | Crear la puerta de entrada. |
   | `AmazonS3FullAccess` | Subir el código a un depósito temporal. |
   | `CloudWatchLogsFullAccess` | Crear el registro de actividad. |
   | `IAMFullAccess` | Crear el rol con que se ejecuta la Lambda. |

3. Al cambiar de búsqueda, las casillas ya marcadas se conservan. Cuando termines, pulsa **Next**.

**3.3 Revisar y crear.** En **Review and create**, en **Permissions summary** deben aparecer las 6 políticas. Pulsa **Create user**. Arriba aparece un aviso verde («User created successfully»).

**3.4 Crear las llaves de acceso.**
1. En la lista de **Users** pulsa el nombre `rfha-deployer`.
2. Abre la pestaña **Security credentials**.
3. Baja hasta la sección **Access keys** y pulsa **Create access key**.
4. En **Use case** elige **Command Line Interface (CLI)**.
5. Más abajo marca la casilla de confirmación («I understand the above recommendation and want to proceed to create an access key») y pulsa **Next**.
6. En **Description tag value** puedes escribir `rfha-demo` (es opcional). Pulsa **Create access key**.
7. Aparecen dos datos: **Access key** (empieza por `AKIA`) y **Secret access key** (pulsa **Show**). Pulsa **Download .csv file** y guárdalo, o copia ambos a un gestor de contraseñas. Después pulsa **Done**.

> **El Secret access key solo se muestra ahora.** Si lo pierdes, hay que crear otra llave. Las dos son el usuario y la contraseña del programa: **nunca las subas a GitHub ni las pegues en chats**.

- **Resultado esperado:** tienes guardados el **Access key ID** y el **Secret access key** del usuario `rfha-deployer`.
- **Si falla:** si el despliegue da `AccessDenied` más adelante, falta alguna de las 6 políticas: entra al usuario, pestaña **Permissions**, y revisa que estén las 6.

---

#### Paso 4. Instalar las herramientas

*El **AWS CLI** es el programa con el que se habla con AWS desde la terminal. **Python 3.12** es la versión que usa la Lambda y con la que corre el script de despliegue. **Git** descarga el código. (No hace falta instalar SAM CLI.)*

**4.1 Abrir PowerShell.** Pulsa la tecla Windows, escribe `PowerShell` y presiona Enter. (También sirve la terminal de VS Code con `Ctrl + ñ`.)

**4.2 Instalar.** Pega los tres comandos, uno por uno. Si pregunta «Do you agree to all the source agreements terms? [Y] Yes», escribe `Y` y Enter.
```powershell
winget install Amazon.AWSCLI
winget install Python.Python.3.12
winget install Git.Git
```

**4.3 Reiniciar la terminal.** **Cierra PowerShell y ábrelo de nuevo** (si no, no reconoce los programas nuevos).

**4.4 Comprobar.**
```powershell
aws --version
py -3.12 --version
git --version
```

- **Resultado esperado:** los tres muestran una versión. Por ejemplo `aws-cli/2.x.x`, `Python 3.12.x` y `git version 2.x.x`.
- **Si falla:**
  - «El término ... no se reconoce»: no cerraste y reabriste PowerShell.
  - `winget` no existe: instala «App Installer» desde la Microsoft Store, o descarga cada programa de su página oficial (AWS CLI en docs.aws.amazon.com, Python en python.org, Git en git-scm.com).
  - `py -3.12` dice que no encuentra Python: la instalación de Python 3.12 no terminó; repítela. **Python 3.12 es necesario** (si solo tienes 3.11, consulta el cambio A del paso 6.2).

---

#### Paso 5. Conectar la terminal con la cuenta

*Aquí se le entregan a la terminal las llaves del paso 3.*

1. En PowerShell escribe:
   ```powershell
   aws configure
   ```
2. Responde las cuatro preguntas (lo que escribes va después de los dos puntos):
   ```
   AWS Access Key ID [None]: AKIA................
   AWS Secret Access Key [None]: ........................................
   Default region name [None]: us-east-2
   Default output format [None]: json
   ```
3. Comprueba la conexión:
   ```powershell
   aws sts get-caller-identity
   ```

- **Resultado esperado:** muestra un texto parecido a este (los números cambian):
  ```json
  {
      "UserId": "AIDA................",
      "Account": "123456789012",
      "Arn": "arn:aws:iam::123456789012:user/rfha-deployer"
  }
  ```
  El `Arn` debe terminar en `user/rfha-deployer`.
- **Si falla:** `InvalidClientTokenId` o `SignatureDoesNotMatch` significa que una llave se copió mal (a veces con un espacio al inicio o al final). Repite `aws configure`.

---

#### Paso 6. Descargar el código y revisar la configuración

**6.1 Descargar.** Elige una carpeta (por ejemplo Documentos) y descarga el proyecto:
```powershell
cd $HOME\Documents
git clone https://github.com/BrayanBMC/RFHA-IES_SD_TGS.git
cd RFHA-IES_SD_TGS
```
Si el equipo indica que lo último todavía está en la rama `dev` (porque aún no se ha unido a `main`), escribe además:
```powershell
git checkout dev
```
Comprueba que estás en la carpeta correcta:
```powershell
dir demo
```
- **Resultado esperado:** la lista incluye `main.py`, `students.py`, `template.yaml`, `requirements.txt` y las carpetas `static` y `tests`.
- **Si falla:** «repository not found» significa que falta acceso al repositorio: pide que te lo den. «No existe la ruta» significa que el `cd` no se ejecutó: repite desde `cd $HOME\Documents`.

**6.2 Revisar el archivo de configuración de AWS (`demo/template.yaml`).**

**Para desplegar normalmente NO hace falta cambiar ningún archivo.** Este es el archivo que AWS lee para saber qué crear. Ábrelo en VS Code (`code .` y luego haz clic en `demo` y `template.yaml`) o en el Bloc de notas. Así debe verse (los comentarios `<-- ...` son solo guía y no van en el archivo):

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: RFHA-IES - Demo del middleware (stack rfha-demo, sin DynamoDB)

Parameters:
  JwtSecret:                          # el secreto (se escribe al desplegar, paso 9)
    Type: String
    NoEcho: true
    MinLength: 32
  DemoMode:                           # 0 = botones apagados, 1 = botones encendidos
    Type: String
    Default: '0'                      # <-- CAMBIO C: aquí se puede dejar '1' por defecto
    AllowedValues: ['0', '1']

Resources:
  DemoApi:                            # la puerta de entrada pública
    Type: AWS::Serverless::HttpApi
    Properties:
      DefaultRouteSettings:
        ThrottlingBurstLimit: 50      # <-- CAMBIO D: máximo de peticiones en ráfaga
        ThrottlingRateLimit: 20       # <-- CAMBIO D: máximo de peticiones por segundo

  DemoFunction:                       # el programa
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: rfha-demo         # <-- CAMBIO B: nombre de la función
      CodeUri: ../build/demo          # NO CAMBIAR: carpeta que arma el script de despliegue
      Handler: main.handler           # NO CAMBIAR: apunta a "handler" en demo/main.py
      Runtime: python3.12             # <-- CAMBIO A: versión de Python de la Lambda
      MemorySize: 256
      Timeout: 10                     # <-- CAMBIO E: segundos máximos por petición
      Environment:
        Variables:
          JWT_SECRET: !Ref JwtSecret
          DEMO_MODE: !Ref DemoMode
      Events:
        Root:                         # la pantalla principal ("/")
          Type: HttpApi
          Properties:
            ApiId: !Ref DemoApi
            Path: /
            Method: ANY
        Any:                          # todas las demás rutas
          Type: HttpApi
          Properties:
            ApiId: !Ref DemoApi
            Path: /{proxy+}
            Method: ANY

  DemoLogGroup:                       # el registro de actividad
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: /aws/lambda/rfha-demo   # <-- CAMBIO B: debe llevar el mismo nombre de la función
      RetentionInDays: 7

Outputs:
  ApiUrl:                             # la dirección pública que se imprime al terminar
    Value: !Sub https://${DemoApi}.execute-api.${AWS::Region}.amazonaws.com
```

**Cambios que solo se hacen si hace falta** (en cada uno: abrir `demo/template.yaml`, buscar la línea, cambiarla y guardar con `Ctrl + S`):

| Cambio | Cuándo hace falta | Qué línea buscar | Cómo debe quedar |
|---|---|---|---|
| **A. Versión de Python** | Solo si el computador tiene Python 3.11 y no 3.12. | `Runtime: python3.12` | `Runtime: python3.11` (y que `py -3.11 --version` funcione). Si se usa el despliegue desde GitHub, cambiar también `python-version` en `.github/workflows/cd-demo.yml`. |
| **B. El nombre ya está en uso** | Si el paso 9 dice que `rfha-demo` ya existe (otro paquete con ese nombre). | `FunctionName: rfha-demo` **y** `LogGroupName: /aws/lambda/rfha-demo` | Cambiar **los dos** al mismo nombre nuevo, por ejemplo `rfha-demo-2` y `/aws/lambda/rfha-demo-2`. Después cambiar también el nombre del *stack* en `scripts/deploy_aws.py` (línea `"stack": "rfha-demo"`) por el mismo nombre nuevo. |
| **C. Dejar los botones encendidos por defecto** | Si se prefiere no escribir `DemoMode` en el paso 9. | `Default: '0'` (debajo de `DemoMode`) | `Default: '1'` |
| **D. Más o menos peticiones por segundo** | Si hay mucha audiencia probando a la vez, o se quiere más protección. | `ThrottlingRateLimit: 20` y `ThrottlingBurstLimit: 50` | Por ejemplo `30` y `60`. |
| **E. Tiempo máximo por petición** | Si la primera consulta en AWS da error de tiempo agotado (*Task timed out*). | `Timeout: 10` | `Timeout: 20` |

**No cambies** `Handler: main.handler` ni `CodeUri: ../build/demo`: están ligados al archivo `demo/main.py` y a la carpeta que arma el script de despliegue. **Tampoco hace falta tocar ningún archivo Python** para desplegar.

---

#### Paso 7. Guardar el secreto en el archivo `.env`

*El secreto es la «tinta» con la que se firman los tokens. Sin él, nadie puede fabricar un token válido. Solo lo deben conocer el equipo y la Lambda. El script de despliegue lo lee de un archivo llamado `.env`, que **no se sube a GitHub**.*

1. Si ya levantaste la demo en tu computador alguna vez, el archivo `.env` ya existe en la carpeta del proyecto y tiene una línea `JWT_SECRET=...`: **no necesitas hacer nada** (el secreto de local y el de AWS serán el mismo).
2. Si no existe, genera un secreto y créalo:
   ```powershell
   py -3.12 -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(48))" | Out-File -Encoding ascii .env
   ```
   Eso crea el archivo `.env` con una línea como `JWT_SECRET=kQ3v9...` (unos 64 caracteres).
3. Comprueba que existe:
   ```powershell
   dir .env
   ```
- **Resultado esperado:** el archivo `.env` aparece en la lista.
- **Reglas:** el secreto debe tener 32 o más caracteres. Si lo vas a compartir con otra persona del equipo, hazlo por un mensaje privado (no por un grupo ni una captura pública). Nunca lo subas a GitHub.
- **Si falla:** si `dir .env` dice que no existe, repite el comando del punto 2 desde la carpeta del proyecto.

---

#### Paso 8. Comprobar que la terminal tiene sesión en AWS

*Antes de desplegar conviene verificar que la terminal sabe en qué cuenta y región está trabajando.*

1. Si la cuenta usa el **inicio de sesión del navegador** (proyecto de la nueva experiencia de AWS), inicia sesión una vez:
   ```powershell
   aws login --region us-east-2 --profile rfha
   ```
   Se abre el navegador; inicia sesión con la cuenta del proyecto. Las credenciales duran 12 horas.
2. Si la cuenta usa **llaves de acceso** (pasos 3 y 5), el perfil se llama `default`; en los comandos siguientes usa `--profile default`.
3. Verifica:
   ```powershell
   aws sts get-caller-identity --profile rfha
   ```
- **Resultado esperado:** muestra el número de cuenta y un `Arn`.
- **Si falla:** `Unable to locate credentials` o `ExpiredToken`: repite el `aws login` (o el paso 5).

---

#### Paso 9. Desplegar con un solo comando

*Desplegar es subir el programa a AWS y dejarlo funcionando. El script `scripts/deploy_aws.py` hace todo: arma el paquete, lo sube y crea los recursos con CloudFormation (un *stack*: conjunto de recursos que se crean y se borran juntos).*

**9.1 Ejecutar el comando.** En PowerShell, dentro de la carpeta del proyecto, pega **una sola línea**.

Para la exposición, **con botones de simulación**:
```powershell
py -3.12 scripts\deploy_aws.py demo --profile rfha --region us-east-2 --demo-mode 1
```
Para dejarla **sin botones**, cambia `--demo-mode 1` por `--demo-mode 0`.

**9.2 Qué hace el script, en orden** (tarda 5 a 15 minutos la primera vez, según la velocidad de internet):

| Orden | Qué hace | Cómo se ve |
|---|---|---|
| 1 | Instala las librerías de la demo para Linux y Python 3.12 en `build\demo`. | Sin mensajes, o solo un aviso de actualización de pip. |
| 2 | Crea el depósito S3 `rfha-deploy-<cuenta>-us-east-2` si no existe. | Un texto con `Location` y `BucketArn`. |
| 3 | Sube el código comprimido al depósito. | `Uploading to ... (100.00%)` |
| 4 | Pide a CloudFormation crear o actualizar el stack `rfha-demo`. | `Waiting for stack create/update to complete` |
| 5 | Imprime la dirección pública. | `LISTO. Dirección pública: https://...` |

**9.3 Resultado esperado.** Termina con una línea como esta; **copia esa dirección, es la URL de la demo**:
```
LISTO. Dirección pública: https://abc123xyz.execute-api.us-east-2.amazonaws.com
```
- **Si falla:**

  | Mensaje | Qué significa | Qué hacer |
  |---|---|---|
  | `No se encontró el AWS CLI` | No está instalado o no se reabrió la terminal. | Paso 4 y reabre PowerShell. |
  | `Falta JWT_SECRET` | No hay `.env` o el secreto es corto. | Paso 7. |
  | `Unable to locate credentials` / `ExpiredToken` | Sin sesión o vencida. | Paso 8. |
  | `AccessDenied` o `not authorized to perform` | Faltan permisos. | Con el usuario del paso 3, revisa sus 6 políticas. |
  | `already exists` (función o grupo de registros) | El nombre `rfha-demo` ya está en uso. | Cambio B del paso 6.2. |
  | `ROLLBACK_COMPLETE` | CloudFormation deshizo todo por un error. | Mira el motivo en la consola: **CloudFormation**, **Stacks**, `rfha-demo`, pestaña **Events**, fila `CREATE_FAILED`, columna **Status reason**. Luego `py -3.12 scripts\deploy_aws.py demo --delete --profile rfha --region us-east-2` y repite el paso 9. |
  | `No matching distribution found` al instalar librerías | Sin internet o antivirus bloqueando. | Revisa la conexión y repite. |
  | `Task timed out` al abrir la página | La primera consulta tardó más que el límite. | Recarga una vez; si persiste, cambio E del paso 6.2. |

**9.4 Si se perdió la URL.** Se puede consultar en cualquier momento:
```powershell
aws cloudformation describe-stacks --stack-name rfha-demo --region us-east-2 --query "Stacks[0].Outputs"
```

---

#### Paso 10. Abrir la demo en el navegador

1. Copia la URL del paso 9 y ábrela en el navegador (sin añadir nada al final).
2. Debe cargar la pantalla **«Consulta federada de historial académico»** y arriba a la derecha decir **Entorno: Nube (AWS)**. *La primera carga puede tardar de 1 a 3 segundos: es el «arranque en frío» de la Lambda, que se despierta al recibir la primera petición.*
3. Haz la primera prueba: en **Estudiante de ejemplo** elige **Brayan Acosta Parrado**, pulsa **Token válido** y luego **Consultar expediente**.

- **Resultado esperado:** los cuatro controles se ponen en verde, aparece la insignia **HTTP 200** y se muestra el expediente.
- **Si falla:**
  - Se ve `{"message":"Not Found"}`: la URL está incompleta, o se desplegó una versión antigua sin la ruta raíz. Descarga el código más reciente (`git pull`) y repite los pasos 8 y 9.
  - Se ve `{"message":"Internal Server Error"}`: error dentro de la Lambda. Mira los registros (sección 4.7).
  - No aparecen los botones ni la lista de estudiantes: se desplegó con `DemoMode=0`. Repite el paso 9 con `"DemoMode=1"`.
  - La página carga pero «Sin conexión»: revisa que la URL no termine en una barra extra ni lleve espacios.

---

#### Paso 11. Recorrer la consola para ver lo que se creó (comprobación)

*No es obligatorio, pero ayuda a entender qué hay en AWS y a explicarlo en la exposición.*

**11.1 El paquete (CloudFormation).**
1. En la consola busca `CloudFormation` y entra. Confirma que arriba a la derecha sigue la región **Ohio**.
2. En el menú izquierdo abre **Stacks** y pulsa **rfha-demo**.
3. Mira el **Status** (arriba): debe decir `CREATE_COMPLETE` (o `UPDATE_COMPLETE`).
4. Pestaña **Resources**: lista lo creado: la API (`AWS::ApiGatewayV2::Api`), la función Lambda, el rol, los permisos y el grupo de registros.
5. Pestaña **Outputs**: aquí está `ApiUrl`. Pestaña **Parameters**: muestra `DemoMode` (el secreto aparece oculto con asteriscos).

**11.2 El programa (Lambda).**
1. Busca `Lambda` y entra. Menú izquierdo: **Functions**. Pulsa **rfha-demo**.
2. Pestaña **Code**: se ve el código subido (`main.py`, `students.py`, carpeta `static`).
3. Pestaña **Configuration**, menú lateral **Environment variables**: están `JWT_SECRET` y `DEMO_MODE`. *Ojo: el secreto se ve aquí a quien tenga acceso a la consola; por eso las llaves y el acceso a la cuenta deben cuidarse.*
4. Pestaña **Configuration**, **General configuration**: muestra memoria (256 MB), tiempo máximo (10 s) y versión de Python (3.12).

**11.3 La puerta de entrada (API Gateway).**
1. Busca `API Gateway` y entra. Menú izquierdo: **APIs**. Pulsa la API cuyo nombre empieza con `rfha-demo` (o la que tenga la misma URL del paso 9).
2. Menú **Routes**: deben verse dos rutas, `ANY /` y `ANY /{proxy+}`, ambas conectadas a la función `rfha-demo`.
3. Menú **Stages**: aparece `$default` con su **Invoke URL**, que es la misma URL del paso 9.

**11.4 El registro de actividad (CloudWatch).**
1. Busca `CloudWatch` y entra. Menú izquierdo: **Logs** y luego **Log groups**.
2. Abre `/aws/lambda/rfha-demo`: en **Retention** debe decir `1 week` (7 días). Dentro hay un *log stream* por cada ejecución con lo que imprimió la Lambda.

---

#### Paso 12. Prueba completa y entrega de la URL

1. Quien conoce el proyecto abre la URL de AWS y repite en la pantalla las **escenas 1, 2, 3, 4, 6 y 7** de la sección 6. Si todas dan lo esperado, la demo en AWS está lista.
2. Quien desplegó envía la **URL** y confirma con qué valor de `DemoMode` desplegó (`1` o `0`).
3. Antes de exponer, abre la URL en una pestaña y haz una consulta de prueba, para que la Lambda esté «despierta».

---

#### Paso 13. Revisar que no se esté cobrando (recomendado)

1. En la consola busca `Billing and Cost Management` y entra.
2. En el menú izquierdo abre **Bills**: el total del mes debe ser **USD 0.00**.
3. En **Free Tier** se ve el uso de los servicios frente a su límite gratuito.

Una demo de este tamaño no debería acercarse a ningún límite. Si aparece algún gasto, ve de inmediato al paso 14 para borrar todo.

---

#### Paso 14. Borrar todo al terminar (importante)

*Borrar evita costos y, si se usó `DemoMode=1`, cierra la puerta que permite generar tokens a quien conozca la URL.*

**14.1 Borrar el paquete.** En PowerShell:
```powershell
py -3.12 scripts\deploy_aws.py demo --delete --profile rfha --region us-east-2
py -3.12 scripts\deploy_aws.py app  --delete --profile rfha --region us-east-2
```
Cada comando espera a que el borrado termine. Esto elimina la Lambda, la API, la tabla de DynamoDB (app final) y el registro de actividad.

**14.2 Comprobar en la consola.** Entra a **CloudFormation**, **Stacks**: `rfha-demo` ya no debe aparecer en la lista (para verlo, el filtro **Deleted** lo muestra con estado `DELETE_COMPLETE`).

**14.3 Borrar el depósito temporal (S3).**
1. Busca `S3` y entra. En **General purpose buckets** busca el que empieza por `rfha-deploy-`.
2. Selecciónalo y pulsa **Empty**. Escribe `permanently delete` para confirmar y pulsa **Empty**.
3. Vuelve a la lista, selecciónalo otra vez y pulsa **Delete**. Escribe el nombre exacto del bucket y confirma.

**14.4 Desactivar las llaves del usuario.**
1. Busca `IAM` y entra. Menú **Users**, pulsa `rfha-deployer`.
2. Pestaña **Security credentials**, sección **Access keys**: pulsa **Actions** y luego **Deactivate**; después **Actions** y **Delete**. Confirma.

- **Resultado esperado:** `rfha-demo` no existe, el bucket no existe y el usuario no tiene llaves activas.

---

### 4.6 Despliegue alternativo desde GitHub (opcional)

Sirve para no instalar nada en el computador. Todo se hace en el sitio web de GitHub, en el repositorio del proyecto.

**Guardar las llaves como secretos (una sola vez):**
1. Abre el repositorio y pulsa la pestaña **Settings**.
2. En el menú izquierdo abre **Secrets and variables** y luego **Actions**.
3. Pulsa **New repository secret**. En **Name** escribe `AWS_ACCESS_KEY_ID` y en **Secret** la llave del paso 3. Pulsa **Add secret**.
4. Repite para `AWS_SECRET_ACCESS_KEY` (el *Secret access key*) y para `DEMO_JWT_SECRET` (el secreto del paso 7).

**Ejecutar el despliegue:**
1. Pulsa la pestaña **Actions**.
2. En la lista de la izquierda elige **CD demo (manual)**.
3. Pulsa **Run workflow** (a la derecha). Elige la rama (`dev` o `main`) y, en **Modo demostración**, elige `1` (con botones) o `0` (sin botones). Pulsa **Run workflow**.
4. Aparece una ejecución nueva con un círculo amarillo; púlsala. Cuando se pone verde (2 a 5 minutos), abre la parte **Summary**: abajo aparece **URL de la demo** con la dirección. También está en el último paso («Mostrar la URL de la demo»).

Borrar todo sigue siendo el paso 14. Si el despliegue falla, abre el paso en rojo para leer el motivo; las causas son las mismas de la tabla del paso 9.

### 4.7 Ver los registros si algo falla

- **Por terminal:**
  ```powershell
  aws logs tail /aws/lambda/rfha-demo --since 30m --profile rfha --region us-east-2
  ```
- **Por consola:** **CloudWatch**, **Log groups**, `/aws/lambda/rfha-demo`, y abre el *log stream* más reciente. Busca líneas con `ERROR` o `Traceback`.

### 4.8 Actualizar la demo si cambia el código

Descarga lo nuevo y repite el despliegue con el mismo secreto:
```powershell
git pull
py -3.12 scripts\deploy_aws.py demo --profile rfha --region us-east-2 --demo-mode 1
```
La URL no cambia.

### 4.9 Problemas frecuentes en AWS

| Qué ves | Causa probable | Qué hacer |
|---|---|---|
| La página principal da `{"message":"Not Found"}` | Se desplegó una versión sin la ruta raíz. | `git pull`, y repetir pasos 8 y 9. |
| Aparece la página pero no los botones | `DemoMode=0`. | Redesplegar con `"DemoMode=1"` (sección 4.8). |
| Salió 403 con un token que debía servir | El secreto de quien genera los tokens no coincide con el desplegado (solo ocurre al pegar tokens a mano). | Con los botones no pasa. Si se pegan tokens, usar el mismo secreto que en el paso 9. |
| La primera carga tarda unos segundos | Arranque en frío de la Lambda. | Es normal. Cargar la página una vez antes de exponer. |
| `AccessDenied` al desplegar | Falta una política al usuario. | Paso 3.2. |
| `Task timed out` | La Lambda superó los 10 segundos. | Cambio E del paso 6.2 y redesplegar. |
| Aparece un cobro en `Bills` | Algo quedó encendido o la cuenta no es de plan Free. | Paso 14 de inmediato y revisar el plan en `Free Tier`. |

### 4.10 Cómo quedó configurado AWS en este proyecto (paso a paso)

Esta sección documenta **exactamente qué se configuró** cuando se desplegó la demo y la app final en el proyecto de AWS del equipo. Sirve para entender, repetir o explicar la arquitectura. Todo se hizo con **un script** y **dos plantillas**, sin entrar a la consola ni instalar SAM CLI.

#### 4.10.1 La forma más fácil de desplegar (3 comandos)

Con el AWS CLI instalado, Python 3.12 y la sesión iniciada:

```powershell
aws login --region us-east-2 --profile rfha          # inicia sesión en el navegador (una vez)
.\.venv\Scripts\python.exe scripts\deploy_aws.py demo --profile rfha --region us-east-2 --demo-mode 1
.\.venv\Scripts\python.exe scripts\deploy_aws.py app  --profile rfha --region us-east-2
```

Cada comando termina con `LISTO. Dirección pública: https://...`. Para comprobar lo desplegado:
```powershell
.\.venv\Scripts\python.exe scripts\smoke_aws.py demo https://<direccion-de-la-demo>
.\.venv\Scripts\python.exe scripts\smoke_aws.py app  https://<direccion-de-la-app>
```
Para borrar todo: `... scripts\deploy_aws.py demo --delete --profile rfha --region us-east-2` (igual con `app`).

#### 4.10.2 Paso a paso de lo que se hizo

**Paso A. Conectar el computador con el proyecto de AWS.**
1. Se instaló el **AWS CLI** (instalador oficial de AWS, versión de usuario, sin administrador).
2. Se ejecutó `aws configure set region us-east-2 --profile rfha`. Todos los recursos regionales deben vivir en la **región del proyecto, Ohio (`us-east-2`)**.
3. Se ejecutó `aws login --region us-east-2 --profile rfha`: abre el navegador, se inicia sesión con la cuenta del proyecto y el CLI guarda **credenciales temporales** (12 horas, renovables hasta 90 días).
4. Se comprobó con `aws sts get-caller-identity --profile rfha`, que devolvió la cuenta del proyecto y el rol con el que se trabaja.
5. Se comprobó el plan con `aws freetier get-account-plan-state`: plan **Free**, activo, con **USD 100 de créditos**.

**Paso B. Dejar el asistente de programación conectado a AWS.** `aws configure agent-toolkit` instaló 25 habilidades de AWS y registró el servidor MCP `aws-mcp` en el editor. Es una ayuda de desarrollo; **no forma parte de la aplicación** ni interviene cuando alguien usa la demo.

**Paso C. Armar el paquete de código.** El script `scripts/deploy_aws.py` crea la carpeta `build/demo` (o `build/app`) con: el código, la pantalla (`static/`) y las librerías de la aplicación instaladas **para Linux y Python 3.12** (la Lambda corre en Linux aunque se arme en Windows). Se usa `pip install --platform manylinux2014_x86_64 --only-binary=:all:` para traer solo paquetes ya compilados.

**Paso D. Crear un depósito S3 para el código.** El script crea (si no existe) el depósito `rfha-deploy-<id-de-la-cuenta>-us-east-2`. Allí se sube el código comprimido para que CloudFormation y Lambda lo lean.

**Paso E. Subir el código y generar la plantilla final.** `aws cloudformation package` comprime la carpeta `build/...`, la sube al depósito y reescribe la plantilla con la ubicación del archivo subido.

**Paso F. Crear los recursos.** `aws cloudformation deploy` lee la plantilla (`demo/template.yaml` o `template.yaml`) y crea el *stack* (`rfha-demo` o `rfha-app`) con los recursos de la tabla siguiente. Usa `CAPABILITY_IAM` (permite crear el rol de la Lambda) y `CAPABILITY_AUTO_EXPAND` (la plantilla usa la sintaxis corta de SAM, que CloudFormation expande).

**Paso G. Leer la dirección pública.** El script consulta las *salidas* del stack (`ApiUrl` o `AppUrl`) y las imprime.

**Paso H. Verificar.** `scripts/smoke_aws.py` hace consultas reales contra la dirección pública (pantalla, rechazos 403, éxito 200, 404, registro 201, duplicado 409, inválido 422).

#### 4.10.3 Qué quedó configurado en cada servicio

| Servicio | Recurso y nombre | Configuración elegida | Por qué |
|---|---|---|---|
| **CloudFormation** | Stacks `rfha-demo` y `rfha-app` | Crea y borra todo junto. | Un solo comando para crear y para eliminar. |
| **S3** | Depósito `rfha-deploy-<cuenta>-us-east-2` | Privado; solo guarda el código comprimido. | Lambda necesita leer el paquete de algún lugar. |
| **IAM** | Un rol de ejecución por Lambda (lo crea la plantilla) | Permiso básico para escribir registros; en la app final, además, permisos de lectura y escritura **solo sobre su tabla**. | Mínimo privilegio. |
| **Lambda (demo)** | Función `rfha-demo` | Python 3.12, 256 MB, 10 s máximo, arquitectura x86_64. Variables de entorno: `JWT_SECRET` (el secreto) y `DEMO_MODE` (`1` o `0`). Manejador `main.handler`. | Ejecuta el middleware de la demo. |
| **Lambda (app)** | Función `rfha-app` | Python 3.12, 256 MB, 15 s. Variables: `REPOSITORY_BACKEND=dynamodb` y `NODES_TABLE` (nombre de la tabla). Manejador `src.app.main.handler`. | Ejecuta el middleware de la app final. |
| **API Gateway** | Una **HTTP API** por stack | Rutas `ANY /` y `ANY /{proxy+}` hacia la Lambda; etapa `$default` con **despliegue automático**; límite de **20 peticiones por segundo** (ráfaga de 50); dirección pública `https://<id>.execute-api.us-east-2.amazonaws.com`. | Es la puerta pública, con HTTPS incluido y sin dominio propio. |
| **DynamoDB** (solo app) | Tabla de nodos (nombre generado por CloudFormation) | Clave de partición `node_id` (texto); modo **bajo demanda** (se paga por uso, sin capacidad reservada); **cifrada en reposo** con el cifrado predeterminado de DynamoDB (clave propiedad de AWS, sin costo; por eso la tabla no muestra un bloque de cifrado propio). Nombre generado: `rfha-app-NodesTable-<código>`. | Guarda las universidades registradas (HU-01). Sin costo fijo. |
| **CloudWatch Logs** | Grupos `/aws/lambda/rfha-demo` y `/aws/lambda/rfha-app` | Retención de **7 días**. | Evita registros que se acumulan y cuestan. |

**No se configuró** (decisiones conscientes, para mantener la demo simple y gratuita): dominio propio, WAF, autorizador de API Gateway (el control de acceso lo hace el middleware en el código), caché, VPC, Secrets Manager (el secreto va en una variable de entorno de la Lambda), ni réplicas de DynamoDB (llegan con HU-08).

#### 4.10.4 Protocolos y formatos que se usan en cada tramo

```
Navegador ──(1)──▶ API Gateway ──(2)──▶ Lambda ──(3)──▶ DynamoDB
                                          └──(4)──▶ CloudWatch Logs
```

| Tramo | Protocolo y formato | Detalle |
|---|---|---|
| **(1) Navegador a API Gateway** | **HTTPS** (HTTP sobre TLS), HTTP/1.1 o HTTP/2 según el navegador. Estilo **REST**, datos en **JSON**. | Métodos `GET` (consultas y archivos de la pantalla) y `POST` (registro y generación de token de prueba). El token viaja en el encabezado `X-Student-Consent-Token`. La conexión va cifrada con TLS (1.2 como mínimo; el navegador puede negociar 1.3). |
| **(2) API Gateway a Lambda** | **Invocación de Lambda** de AWS (integración tipo *proxy*), **formato de carga 2.0** en JSON. | API Gateway empaqueta la petición HTTP en un evento JSON; la Lambda devuelve otro JSON con código de estado, encabezados y cuerpo. Va por la red interna de AWS, firmado con credenciales internas. |
| **Dentro de la Lambda** | **ASGI** | **Mangum** traduce el evento de API Gateway al estándar ASGI que entiende **FastAPI**. No usa red. |
| **(3) Lambda a DynamoDB** (solo app) | **HTTPS** con la **API JSON de DynamoDB**, firmada con **Signature V4**. | `boto3` firma cada llamada con las credenciales temporales del rol de la Lambda. Operaciones: `Scan` (buscar NIT) y `PutItem` (crear nodo). |
| **(4) Lambda a CloudWatch Logs** | Interno de AWS, automático. | Lo que la función imprime y una línea de resumen por ejecución. |
| **Permiso del estudiante** | **JWT** (RFC 7519) firmado con **HMAC-SHA256 (HS256)**. | Lleva el estudiante y la fecha de vencimiento. Lo valida el middleware con el secreto de su variable de entorno. |
| **Despliegue (CLI a AWS)** | **HTTPS** con **Signature V4**. | El AWS CLI usa las credenciales temporales de `aws login`. |
| **Inicio de sesión (`aws login`)** | **OAuth 2.0 con PKCE** en el navegador. | El CLI nunca ve la contraseña; recibe credenciales temporales. |

> **Para la exposición:** el protocolo del servicio web es **HTTPS + REST + JSON**. API Gateway es el *transportista* (terminación TLS y enrutamiento) y la Lambda es donde vive el *middleware* (validación del permiso y respuesta).

#### 4.10.5 Qué permisos usa cada pieza

| Quién | Qué puede hacer |
|---|---|
| **Persona que despliega** | Crear stacks, funciones, APIs, tablas y depósitos en el proyecto (rol de administración del proyecto). |
| **Rol de la Lambda `rfha-demo`** | Solo escribir sus registros. No toca ninguna otra cosa de AWS. |
| **Rol de la Lambda `rfha-app`** | Escribir sus registros y leer/escribir **su** tabla. Nada más. |
| **Cualquier visitante** | Llamar a la dirección pública. Sin token, el middleware lo rechaza (salvo en la demo con `DemoMode=1`, que permite generar tokens de prueba). |

#### 4.10.6 Resultado del despliegue real (noviembre de 2026)

Se desplegaron los dos stacks en el proyecto del equipo (región Ohio, `us-east-2`) y se comprobaron con `scripts/smoke_aws.py` contra las direcciones públicas. **Las direcciones no se publican en este repositorio** porque la demo se desplegó con `DemoMode=1` (quien las conozca puede generar tokens de prueba); se entregan al equipo por mensaje privado.

| Comprobación | Resultado | Tiempo |
|---|---|---|
| **Demo:** pantalla principal | 200 | 7,4 s (arranque en frío) |
| **Demo:** archivo estático (`app.js`) | 200 | 0,3 s |
| **Demo:** sin token | 403 | 0,3 s |
| **Demo:** generar token válido y expirado (modo demostración) | 200 | 0,3 s |
| **Demo:** token válido | 200 con el expediente | 0,3 s |
| **Demo:** token de otro estudiante | 403 | 0,3 s |
| **Demo:** token expirado | 403 | 0,3 s |
| **Demo:** estudiante inexistente | 404 | 0,3 s |
| **App:** formulario `/registro-nodo` | 200 | 2,3 s (arranque en frío) |
| **App:** registro de un nodo | 201 con estado `PENDIENTE_APROBACION` y código `IES-XXXXXXXX` | 2,9 s (primera escritura en DynamoDB) |
| **App:** el mismo NIT otra vez | 409 | 0,35 s |
| **App:** datos inválidos | 422 | 0,3 s |

**Qué muestran estos números:** la primera petición a cada función tarda varios segundos porque Lambda debe crear su entorno de ejecución (arranque en frío); las siguientes responden en unos 0,3 s, dentro de la meta de menos de 1,5 s del levantamiento de requerimientos. Que el mismo NIT devolviera `409` confirma que el registro de prueba quedó guardado en DynamoDB (el contador de elementos de la consola se actualiza solo cada varias horas, así que no es una prueba inmediata). Ese registro de prueba se elimina al borrar el stack.

**Comprobado contra AWS** con comandos de solo lectura: los recursos de cada stack (API, etapa, función, rol, permisos, registros y tabla), la configuración de las dos Lambdas (Python 3.12, 256 MB, 10 y 15 s, x86_64, variables de entorno), el tipo de API (HTTP), la tabla (clave `node_id`, modo bajo demanda, activa) y la retención de registros (7 días).

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

### 6.5 Qué hace Amazon (AWS) en cada escena y cómo se relaciona con el middleware

Esta sección solo aplica al **Plan B** (la demo en AWS). Explica qué servicio de Amazon interviene en cada prueba y qué parte hace el middleware.

#### 6.5.1 Las herramientas que se usaron

**Para desplegar (se usan una vez):**

| Herramienta | Qué es | Qué hizo en este proyecto |
|---|---|---|
| **AWS CLI** | Programa de terminal para hablar con AWS. | Inició la sesión (`aws login`), verificó la identidad (`aws sts get-caller-identity`) y consultó el estado del plan. |
| **AWS Agent Toolkit** | Conjunto de habilidades y un servidor MCP que conecta el editor con AWS. | Dejó configurado el acceso del asistente de programación a la documentación y a las guías de AWS. No interviene cuando la demo funciona. |
| **Script `scripts/deploy_aws.py`** | Programa del proyecto que automatiza el despliegue usando solo el AWS CLI y Python. | Arma el paquete con sus librerías, lo sube y crea el stack. No hace falta SAM CLI. |
| **AWS CloudFormation** | El servicio que crea y borra los recursos juntos, como un *stack*. | Crea el paquete `rfha-demo` (y `rfha-app` para la app final) a partir de `template.yaml`. |
| **Amazon S3** | Almacenamiento de archivos. | Guarda temporalmente el código empaquetado para que Lambda lo descargue. No lo usa la demo en ejecución. |
| **AWS IAM** | Usuarios, roles y permisos. | Define quién puede desplegar y el **rol de ejecución** con el que corre la Lambda (solo puede escribir sus registros; la app final además puede leer y escribir su tabla). |

**Para funcionar (se usan en cada consulta):**

| Servicio | Qué hace en la demo | Relación con el middleware |
|---|---|---|
| **Amazon API Gateway** (tipo HTTP API) | Es la puerta pública con HTTPS. Recibe la petición, comprueba la ruta y el límite de 20 peticiones por segundo, y se la entrega a la Lambda. Devuelve la respuesta al navegador. | Es el **transportista**: el cliente solo conoce su dirección. **No valida permisos**: eso lo hace el código. |
| **AWS Lambda** (Python 3.12) | Ejecuta el programa bajo demanda: arranca un entorno, ejecuta el código y lo deja dormir. | **Aquí vive el middleware.** El código de `demo/main.py` revisa los 4 controles dentro de la Lambda. |
| **Rol de ejecución (IAM)** | Da a la Lambda el permiso mínimo para escribir sus registros. | Sin este rol la Lambda no podría registrar su actividad. |
| **Amazon CloudWatch Logs** | Guarda lo que imprime la Lambda y una línea de resumen por ejecución (duración, memoria usada). Se borra a los 7 días. | Permite ver, consulta por consulta, que el middleware se ejecutó. |
| **Variables de entorno de Lambda** | Guardan `JWT_SECRET` y `DEMO_MODE`. | De ahí lee el middleware el secreto con el que verifica la firma del token. |
| **Amazon DynamoDB** (solo app final) | Base de datos de claves y valores. | Guarda los nodos (universidades) registrados en HU-01. En la demo no se usa: los estudiantes están en memoria. |

#### 6.5.2 Lo que ocurre en AWS en *cada* consulta

1. **API Gateway** recibe la petición HTTPS y cifra/descifra el tráfico (TLS).
2. **API Gateway** busca una ruta que coincida (`ANY /` o `ANY /{proxy+}`). Si hay más de 20 peticiones por segundo responde `429` sin llegar a la Lambda.
3. **Lambda** recibe un evento con la petición. Si no hay un entorno caliente, lo crea (**arranque en frío**, 1 a 3 segundos); si lo hay, lo reutiliza.
4. **Mangum** (dentro de la Lambda) convierte el evento de API Gateway en una petición normal para **FastAPI**.
5. El **middleware** (FastAPI + el código de la demo) revisa los 4 controles y decide.
6. **Lambda** devuelve el resultado a **API Gateway**, que lo envía al navegador.
7. **CloudWatch Logs** guarda el resumen de la ejecución. **Se factura** una invocación de Lambda y una petición de API Gateway (dentro del plan gratuito).

> **Idea clave:** el rechazo `403` y el `404` los produce **el código del middleware dentro de la Lambda**, no API Gateway. Se distinguen porque las respuestas del middleware traen `{"detail": "..."}`; si fuera API Gateway quien rechaza, el texto sería `{"message": "..."}`.

#### 6.5.3 Qué hace AWS en cada escena

| Escena | Qué hace AWS | Qué decide el middleware | Servicios que intervienen |
|---|---|---|---|
| **1. Consulta exitosa** | Recorre el flujo completo: puerta, Lambda, respuesta. La Lambda tarda unos milisegundos; el resto es red. | Pasa los 4 controles y devuelve `200` con el expediente. | API Gateway, Lambda, CloudWatch |
| **2. Sin token** | La petición llega igual. **AWS no la rechaza**: no tiene autorizador configurado. | Corta en el control 1 y devuelve `403`; no busca al estudiante. | API Gateway, Lambda, CloudWatch |
| **3. Token expirado** | La Lambda compara la fecha de vencimiento del token con **el reloj de AWS**, que está sincronizado. | Control 2: `403` «ha expirado». | API Gateway, Lambda |
| **4. Token alterado** | AWS entrega la petición. La Lambda recalcula la firma con el secreto guardado en su variable de entorno. | Control 2: la firma no coincide, `403`. | API Gateway, Lambda, variables de entorno |
| **5. Texto que no es token** | Igual que la escena 4: el texto llega a la Lambda. | Control 2: no se puede abrir, `403`. | API Gateway, Lambda |
| **6. Token de otra persona** | AWS no interviene en la decisión; solo transporta. El secreto vuelve a leerse de la variable de entorno. | Control 3: el estudiante del token no coincide con el de la dirección, `403`. | API Gateway, Lambda, variables de entorno |
| **7. Estudiante inexistente** | La Lambda busca en memoria (en la demo no usa DynamoDB). El `404` es del código, no de API Gateway. | Control 4: no encuentra el código, `404`. | API Gateway, Lambda |
| **8. Código mal escrito** | **AWS no participa**: la pantalla frena el envío en el navegador, por eso no hay petición, ni registro, ni costo. | No interviene. | Ninguno |
| **9. Tres universidades** | Tres peticiones iguales. Cada una invoca la Lambda de nuevo; pueden usar el mismo entorno caliente. | Mismos controles y mismo formato para las tres. | API Gateway, Lambda |
| **10. Homologación** | **Solo la consulta inicial usa AWS.** Al mover la nota mínima se calcula en el navegador con los datos ya recibidos: no hay nuevas peticiones ni costo. | Entregó los datos con campos uniformes, que hacen posible la comparación. | API Gateway, Lambda (una vez) |
| **11. Graduado** | Igual que la escena 1; el tamaño de la respuesta cambia muy poco. | Entrega los campos adicionales (título y fecha de grado). | API Gateway, Lambda |
| **12. Retirado** | Igual que la escena 1. | No filtra por estado académico. | API Gateway, Lambda |
| **13. Varias consultas seguidas** | Si llegan a la vez, Lambda puede crear **varios entornos en paralelo** y cada uno atiende una. Escala sola. | Sin estado: revisa cada petición desde cero. | API Gateway, Lambda (escalado) |
| **14. JSON y curl** | El JSON lo arma la Lambda y viaja por la dirección pública de API Gateway; `curl` usa esa misma dirección. | La respuesta es un servicio REST estándar. | API Gateway, Lambda |
| **15. Servidor apagado** | En Plan B equivale a que AWS no responda: si la Lambda falla, API Gateway devuelve `500/502/503` con texto `{"message": ...}`; si se supera el límite, `429`. | No llega a ejecutarse. | API Gateway |

#### 6.5.4 Dónde verlo en la consola de AWS

Después de hacer una escena, entra a la consola de AWS (región **Ohio, us-east-2**):

| Para ver | Dónde |
|---|---|
| Que la Lambda se ejecutó | **CloudWatch**, **Log groups**, `/aws/lambda/rfha-demo`, el *log stream* más reciente: aparecen líneas `START`, `END` y `REPORT` (duración, memoria, y `Init Duration` si fue arranque en frío). |
| Cuántas peticiones y errores | **Lambda**, la función `rfha-demo`, pestaña **Monitor**: invocaciones, duración y errores. |
| Las rutas de la puerta | **API Gateway**, la API de la demo, **Routes**: `ANY /` y `ANY /{proxy+}`. |
| Los recursos del paquete | **CloudFormation**, el *stack* `rfha-demo`, pestaña **Resources**. |
| El secreto y el modo | **Lambda**, **Configuration**, **Environment variables**. |
| El gasto | **Billing and Cost Management**, **Free Tier** o **Bills**. |

#### 6.5.5 App final en AWS: qué hace AWS al registrar una universidad (HU-01)

La app final usa los mismos servicios más **DynamoDB**.

| Caso en el formulario `/registro-nodo` | Qué hace AWS | Qué hace el middleware |
|---|---|---|
| **Registro exitoso** | API Gateway entrega la petición `POST` a la Lambda `rfha-app`. La Lambda lee la tabla de DynamoDB (`Scan`) para comprobar el NIT y luego escribe el nodo (`PutItem`). | Valida los datos (Pydantic), genera el código `IES-XXXXXXXX` y responde `201`. |
| **NIT duplicado** | La Lambda ejecuta la lectura (`Scan`) y encuentra el NIT. **No escribe nada.** | Responde `409`. |
| **Datos inválidos** | La petición llega a la Lambda, **pero no se consulta DynamoDB**. | Pydantic rechaza los datos y responde `422` sin tocar la base. |
| **Abrir el formulario** | API Gateway y Lambda sirven la página y sus archivos estáticos (HTML, CSS, JS); no hay S3 ni CloudFront. | Añade cabeceras de seguridad (CSP). |

La tabla se cifra en reposo con una clave administrada por AWS y se factura por uso (modo bajo demanda). La Lambda solo tiene permiso sobre **su** tabla.

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
| `DemoFunction` | La Lambda `rfha-demo`: Python 3.12, 256 MB, 10 segundos máximo. |
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
| En AWS no aparecen los botones ni la lista | Se desplegó con `DemoMode=0`. | Usa el Plan A para las pruebas con clics, o redesplega con `DemoMode=1` (sección 4.8). |
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
python scripts/check_demo.py https://abc123xyz.execute-api.us-east-2.amazonaws.com
```
Debe terminar con `TODO BIEN`. Para AWS, antes: `py -3.12 -m pip install PyJWT` y `$env:JWT_SECRET = "<el secreto>"`.

**Una consulta suelta** (en PowerShell se usa `curl.exe`):
```powershell
curl.exe -i -H "X-Student-Consent-Token: <TOKEN>" http://127.0.0.1:8000/api/v1/federated/academic-history/20262678029
```
Sin el encabezado `-H ...` la respuesta es 403.

**Documentación interactiva de la API:** `http://127.0.0.1:8000/docs` (se puede probar el servicio desde ahí).

**Pruebas automáticas:** las ejecuta GitHub en cada subida de código. Localmente: `pytest`.
