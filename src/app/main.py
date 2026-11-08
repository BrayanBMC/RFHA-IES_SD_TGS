from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from mangum import Mangum

from src.app.routers import nodes

STATIC_DIR = Path(__file__).resolve().parent / "static"
PAGE_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; "
        "base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}

app = FastAPI(
    title="RFHA-IES - Red Federada de Historiales Académicos",
    description="Middleware federado (app final).",
)
app.include_router(nodes.router)

# Interfaz web (HTML/CSS/JS estáticos, sin build). Se amplía con cada historia (HU-10).
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def home():
    return RedirectResponse(url="/registro-nodo")


@app.get("/registro-nodo", include_in_schema=False)
async def registro_nodo_page():
    """HU-01: formulario de inscripción de un nuevo nodo institucional."""
    return FileResponse(STATIC_DIR / "registro-nodo.html", headers=PAGE_HEADERS)


# Punto de entrada para AWS Lambda.
handler = Mangum(app, lifespan="off")
