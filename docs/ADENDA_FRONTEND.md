# Adenda al levantamiento de requerimientos: Interfaz web (frontend)

Versión 2.1 del documento de requerimientos de RFHA-IES (noviembre 2026). Complementa las secciones C (alcance), E (requerimientos funcionales), F (no funcionales), G (historias de usuario) y H (arquitectura). Corrige el vacío detectado en `docs/BRECHAS.md` B10: el alcance incluía una aplicación web responsiva, pero no existía una historia de usuario para ella.

## 1. Alcance

- **Incluido:** una aplicación web responsiva de una sola página por pantalla (HTML, CSS y JavaScript nativos), servida por la misma Lambda que la API. Una versión para la **demo** (ya construida) y otra para la **app final** (HU-10).
- **Excluido:** aplicaciones móviles nativas, frameworks de frontend, paso de compilación (build), CDN y hosting separado (S3/CloudFront).
- **Por qué sin framework:** menos piezas, cero dependencias, mejor rendimiento y seguridad, y nada que desplegar aparte.

## 2. Requerimientos funcionales de la interfaz

| ID | Requerimiento | Prioridad | Criterio de aceptación |
|---|---|---|---|
| **RF-11** | **Consulta visual del historial.** El funcionario ingresa el código del estudiante y el token y ve el expediente. | Alta | Muestra nombre, universidad, programa, promedio y tabla de asignaturas con nota. Hecho en la demo. |
| **RF-12** | **Visualización de la validación del middleware.** La interfaz muestra en qué paso se aceptó o rechazó la consulta. | Media | Cuatro pasos (token presente, firma y vigencia, titular, búsqueda) con estado aprobado, rechazado u omitido. Hecho en la demo. |
| **RF-13** | **Registro de universidad desde la web** (HU-01). | Alta | Formulario con validación en pantalla y mensaje con el `node_id` y el estado `PENDIENTE_APROBACION`. |
| **RF-14** | **Panel del administrador general** (HU-02). | Alta | Lista de solicitudes pendientes y botón de aprobar; muestra la API Key una sola vez. |
| **RF-15** | **Panel del nodo** (HU-03). | Media | Carga de un JSON de historiales con vista previa y resultado de la sincronización. |
| **RF-16** | **Portal del estudiante** (HU-04 y HU-05). | Alta | Genera un token indicando la universidad destino, lista los tokens activos y permite revocarlos. |
| **RF-17** | **Indicador de fuente de datos** (HU-08). | Media | Muestra si el dato vino del nodo origen o de la réplica (`X-Data-Source`). |
| **RF-18** | **Consulta de auditoría** (HU-09). | Media | Tabla filtrable de consultas con fecha, universidad consultante y resultado. |
| **RF-19** | **Modo demostración.** Botones que simulan el consentimiento del estudiante. | Media | Solo visible con `DEMO_MODE=1`; apagado por defecto y en AWS. Hecho en la demo. |

## 3. Requerimientos no funcionales de la interfaz

| ID | Categoría | Requerimiento |
|---|---|---|
| **RNF-F1** | Accesibilidad | Cumplir WCAG 2.2 nivel AA: HTML semántico, etiquetas, foco visible, uso completo con teclado, anuncios para lector de pantalla (`aria-live`), contraste mínimo 4.5:1, objetivos táctiles de 44 px o más, información no basada solo en color. |
| **RNF-F2** | Adaptabilidad | Diseño mobile-first que funciona desde 320 px de ancho. |
| **RNF-F3** | Apariencia | Modo claro y oscuro automático según el sistema; respeto a `prefers-reduced-motion` y `forced-colors`. |
| **RNF-F4** | Seguridad | CSP estricta sin scripts ni estilos en línea; `nosniff`; `Referrer-Policy: no-referrer`; contenido dinámico insertado como texto (sin `innerHTML`); tokens solo en memoria (nunca en `localStorage`). |
| **RNF-F5** | Rendimiento | Sin dependencias externas ni fuentes de terceros; LCP menor a 2.5 s en conexión normal. |
| **RNF-F6** | Compatibilidad | Navegadores actuales de escritorio y móvil con soporte de CSS `light-dark()`, anidamiento y módulos ES. |
| **RNF-F7** | Idioma | Interfaz en español; números y fechas en formato `es-CO`. |
| **RNF-F8** | Costo | Cero recursos AWS adicionales: los archivos estáticos se sirven desde la misma Lambda. |
| **RNF-F9** | Mantenibilidad | Un único sistema de diseño (`styles.css`) con variables CSS; la app final lo reutiliza. |

## 4. Historia de usuario

```
+-----------------------------------------------------------------------------------+
| HU-10: Interfaz web de la Red Federada                                            |
+-----------------------------------------------------------------------------------+
| Como: Funcionario, estudiante o administrador de la red                           |
| Quiero: Usar las funciones del sistema desde una interfaz web clara y accesible   |
| Para: No depender de herramientas técnicas para consultar, autorizar y administrar.|
+-----------------------------------------------------------------------------------+
| Estimación: 13 Puntos (Talla XL) | Prioridad: Media | Cobertura: RF-11 a RF-19    |
| Dependencias: HU-01 a HU-09 completas. Se entrega después de la HU-09.             |
+-----------------------------------------------------------------------------------+
| Criterios de Aceptación (Given / When / Then):                                    |
| - GIVEN el usuario abre la aplicación en un celular o un computador,              |
|   WHEN navega solo con teclado o con lector de pantalla,                          |
|   THEN puede completar todas las acciones y recibe anuncios del resultado.        |
| - GIVEN el funcionario ingresa un código de estudiante y un token válido,         |
|   WHEN pulsa "Consultar expediente",                                              |
|   THEN ve el historial y la fuente de datos; con un token inválido ve el paso     |
|   donde fue rechazado y el mensaje de error.                                      |
| - GIVEN el estudiante inició sesión, WHEN genera o revoca un token,               |
|   THEN la lista de tokens activos se actualiza y se confirma la acción.           |
| - GIVEN el administrador general, WHEN aprueba una solicitud de nodo,             |
|   THEN ve la API Key una sola vez y el nodo pasa a ACTIVO.                        |
| - GIVEN cualquier pantalla, WHEN falla la red,                                    |
|   THEN se muestra un mensaje claro sin perder lo escrito.                         |
+-----------------------------------------------------------------------------------+
```

### Pantallas de HU-10
1. Registro de universidad.
2. Panel del administrador general.
3. Panel del nodo (carga de historiales).
4. Portal del estudiante (tokens).
5. Consulta del funcionario.
6. Auditoría.

## 5. Arquitectura del frontend

```
Navegador ──HTTPS──▶ API Gateway ──▶ Lambda (FastAPI + Mangum)
                                       ├─ /                → index.html (estático)
                                       ├─ /static/*        → styles.css, app.js
                                       └─ /api/v1/...      → API REST (JSON)
```

- **Misma Lambda, mismo origen:** no hace falta CORS y las cabeceras de seguridad se controlan en un solo lugar.
- **Estructura:** `demo/static/` (hecho) y `src/app/static/` (HU-10). Sin importar entre carpetas; el diseño se copia y extiende.

## 6. Pruebas del frontend

- **Automáticas (CI):** la página responde 200 y tiene `lang="es"` y `viewport`; CSP presente; sin `<style>`, `<script>` en línea ni `onclick`; estáticos con 200; el modo demostración está apagado por defecto y la generación de tokens da 404 cuando está apagado.
- **Manuales antes de aprobar HU-10:** recorrido solo con teclado, prueba con lector de pantalla (NVDA), modo oscuro, pantalla de 320 px y zoom al 200 %.

## 7. Riesgos

| Riesgo | Mitigación |
|---|---|
| Sin framework, el código de la interfaz puede crecer desordenado. | Un módulo por pantalla y un solo `styles.css` con variables; si crece, evaluar una librería ligera. |
| El navegador del evaluador no soporta CSS moderno (`light-dark()`). | Probar en navegadores actuales antes de la exposición. |
| Modo demostración activo en AWS permite generar tokens. | Apagado por defecto (`DemoMode=0`); activarlo solo para ensayar y volver a apagarlo. |

## 8. Trazabilidad

| Requerimiento | Estado | Dónde |
|---|---|---|
| RF-11, RF-12, RF-19 | Hecho en la demo | `demo/static/`, `docs/DEMO.md` |
| RF-13 | Hecho en HU-01 | `src/app/static/registro-nodo.html`, `docs/historias/HU-01.md` |
| RF-14 a RF-18 | Pendiente (HU-10) | `src/app/static/` |
| RNF-F1 a RNF-F9 | Aplicados en la demo; se verifican en HU-10 | `docs/PROMPT-AGENTE-RFHA-IES.md`, sección 10 |
