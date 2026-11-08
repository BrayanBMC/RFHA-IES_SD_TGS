# RFHA-IES — Red Federada de Historiales Académicos

Proyecto final de Sistemas Distribuidos y Teoría General de Sistemas (Universidad Distrital, Ingeniería en Telemática).
Fuente de verdad: `levantamiento_de_requerimientos_proyecto_final.md`.

## Estructura

| Carpeta | Contenido |
|---|---|
| `demo/` | Demo del middleware para la exposición. Autónoma, puerto **8000**. Incluye la interfaz web en `demo/static/`. |
| `src/app/` | App final. Puerto **8001**. Su interfaz web (`src/app/static/`) llega con HU-10. |
| `tests/` | Pruebas de la app final. |
| `scripts/` | Utilidades (`generate_token.py`, `check_demo.py`). |
| `thunder-tests/` | Colecciones de Thunder Client (carpetas "Demo" y "App final"). |
| `docs/` | Decisiones, brechas, guía de AWS, documentación por historia. |

`demo/` y `src/app/` no se importan entre sí.

## Primer arranque en un PC nuevo

Requisitos: **Python 3.11 o 3.12**, Git y VS Code. (Python 3.15 puede fallar al instalar dependencias.)

### Windows (PowerShell)

```powershell
git clone https://github.com/BrayanBMC/RFHA-IES_SD_TGS.git
cd RFHA-IES_SD_TGS
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
pytest
code .
```

Si PowerShell bloquea la activación: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

### macOS / Linux

```bash
git clone https://github.com/BrayanBMC/RFHA-IES_SD_TGS.git
cd RFHA-IES_SD_TGS
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest
code .
```

Edita `.env` y pon un `JWT_SECRET` propio:
`python -c "import secrets; print(secrets.token_urlsafe(48))"`

### Levantar las APIs

```bash
uvicorn demo.main:app --reload --port 8000        # demo
uvicorn src.app.main:app --reload --port 8001     # app final (desde HU-01)
```

Documentación interactiva: `http://127.0.0.1:8000/docs` y `http://127.0.0.1:8001/docs`.

### Thunder Client

1. Al abrir el proyecto, VS Code propone instalar las extensiones recomendadas. Acepta.
2. Las colecciones se cargan solas desde `thunder-tests/` (`thunder-client.saveToWorkspace` ya está activo en `.vscode/settings.json`).
3. Cambia entre entornos `Local` y `AWS` en el selector de Environment.

Cada request también está documentada como `curl` en `docs/DEMO_MARTES.md` y en `docs/historias/`.

## Pruebas

```bash
pytest                 # todo
pytest demo/tests      # solo demo
pytest tests           # solo app final
```

## Demo en un comando

```powershell
.\run-demo.ps1          # Windows
bash run-demo.sh        # macOS / Linux
```

Si PowerShell bloquea scripts: `.\run-demo.cmd`. Cuando salga "DEMO LISTA", abre **http://127.0.0.1:8000** (interfaz web).

Guía completa (local, AWS, interfaz y explicación del código): `docs/DEMO.md`.

## Documentación

- `docs/DEMO.md`: demo paso a paso (local y AWS) y explicación del código.
- `docs/PROMPT-AGENTE-RFHA-IES.md`: prompt de trabajo del agente (v2, incluye frontend).
- `docs/ADENDA_FRONTEND.md`: requerimientos de la interfaz web (RF-11 a RF-19, RNF-F1 a F9, HU-10).
- `docs/DECISIONES.md`: decisiones tomadas.
- `docs/BRECHAS.md`: faltantes y ambigüedades del documento.
- `docs/AWS_PASO_A_PASO.md`: guía para el compañero de AWS (se crea con la demo).
- `docs/DEMO_MARTES.md`: guion y lista de verificación de la exposición.

## Reglas del repositorio

- Un commit/PR por historia de usuario, en rama `feature/hu-xx-nombre`, con Conventional Commits.
- Nunca subir `.env`, claves ni credenciales de AWS.
