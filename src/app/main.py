from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from mangum import Mangum

from src.app.routers import admin, audit, federated, nodes, students, sync

STATIC_DIR = Path(__file__).resolve().parent / "static"
PAGE_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; "
        "base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}

# Pantallas de la app final: ruta -> archivo HTML. Se amplían con cada historia (HU-10).
PAGES = {
    "/": "inicio.html",  # menú de inicio
    "/registro-nodo": "registro-nodo.html",  # HU-01
    "/admin": "admin.html",  # HU-02
    "/panel-nodo": "panel-nodo.html",  # HU-03
    "/portal-estudiante": "portal-estudiante.html",  # HU-04 y HU-05
    "/consulta": "consulta.html",  # HU-06, HU-07 y HU-08
    "/auditoria": "auditoria.html",  # HU-09
    "/reportes": "reportes.html",   # HU-Admin-Reports
}

app = FastAPI(
    title="RFHA-IES - Red Federada de Historiales Académicos",
    description="Middleware federado (app final).",
)
app.include_router(nodes.router)
app.include_router(admin.router)
app.include_router(sync.router)
app.include_router(students.router)
app.include_router(federated.router)
app.include_router(audit.router)

# Interfaz web (HTML/CSS/JS estáticos, sin build).
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _page(filename: str):
    async def serve():
        return FileResponse(STATIC_DIR / filename, headers=PAGE_HEADERS)

    return serve


for _path, _file in PAGES.items():
    app.add_api_route(_path, _page(_file), methods=["GET"], include_in_schema=False)

# Punto de entrada para AWS Lambda.
handler = Mangum(app, lifespan="off")
