from fastapi import FastAPI
from mangum import Mangum

from src.app.routers import nodes

app = FastAPI(
    title="RFHA-IES - Red Federada de Historiales Académicos",
    description="Middleware federado (app final).",
)
app.include_router(nodes.router)

# Punto de entrada para AWS Lambda.
handler = Mangum(app, lifespan="off")
