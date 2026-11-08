# Demo del Middleware: guía para la exposición

Cubre HU-06 y HU-07 en versión mínima. Dos planes con el mismo código:

- **Plan A: local.** `uvicorn` en tu PC. No depende de internet ni de AWS.
- **Plan B: AWS.** API Gateway + Lambda (stack `rfha-demo`). Guía en `docs/AWS_PASO_A_PASO.md`.

## Levantar todo en 3 comandos (Plan A)

Con el entorno virtual activo (ver README):

```bash
python scripts/generate_token.py                       # 1. imprime token válido y token expirado
uvicorn demo.main:app --port 8000                      # 2. levanta la API
python scripts/check_demo.py http://127.0.0.1:8000     # 3. (otra terminal) verifica los 3 escenarios
```

En Thunder Client, entorno `Local`: pega los dos tokens en las variables `validToken` y `expiredToken`.

## Los tres escenarios (curl de respaldo)

```bash
BASE=http://127.0.0.1:8000
URL=$BASE/api/v1/federated/academic-history/20262678029

curl -i $URL                                                     # 403 sin token
curl -i -H "X-Student-Consent-Token: <TOKEN_EXPIRADO>" $URL      # 403 expirado
curl -i -H "X-Student-Consent-Token: <TOKEN_VALIDO>" $URL        # 200 con historial
```

En PowerShell usa `curl.exe` (no `curl`, que es un alias de otra cosa).

## Qué decir en cada paso (7 minutos)

1. **Problema y rol del middleware (1.5 min).** Las IES son islas de datos. El middleware es el *transportista*: el cliente llama a una sola URL y no conoce IP, ubicación ni motor de base de datos del nodo.
2. **Sin token → 403 (2 min).** Ejecuta la request 1. "El middleware corta la petición antes de tocar los datos. Sin consentimiento del estudiante no hay acceso."
3. **Token expirado → 403 (1 min).** Ejecuta la request 3. "El consentimiento es temporal."
4. **Token válido → 200 (2 min).** Ejecuta la request 2. "Se valida la firma en Lambda, se localiza el dato y se entrega en JSON."
5. **Cierre (0.5 min).** Transparencia de **acceso** (misma API REST para todos) y de **ubicación** (el cliente no sabe dónde está el dato).

## Lista de verificación: 10 minutos antes de la clase

- [ ] Entorno virtual activo y `pip install -r requirements.txt` hecho.
- [ ] `.env` con `JWT_SECRET` (el mismo valor que la Lambda de AWS).
- [ ] `python scripts/generate_token.py`: tokens **válido y expirado** copiados a Thunder Client.
- [ ] `uvicorn demo.main:app --port 8000` corriendo.
- [ ] `python scripts/check_demo.py http://127.0.0.1:8000` → TODO BIEN.
- [ ] Plan B: **calentamiento**. Una petición a la URL de AWS (la Lambda tarda en el primer uso por cold start). Luego `python scripts/check_demo.py <url-aws>` → TODO BIEN.
- [ ] Thunder Client: selector de entorno visible. Cambiar entre `Local` y `AWS` solo cambia `baseUrl`; las 3 requests son las mismas.
- [ ] Los tokens válidos duran 24 h: genéralos el mismo día.

## Si algo falla en vivo

| Síntoma | Qué hacer |
|---|---|
| Local no arranca | Cambia al entorno `AWS` en Thunder Client. |
| AWS tarda o da 5xx | Cambia al entorno `Local`. Si es la primera petición, repítela (cold start). |
| 200 esperado pero llega 403 | El token expiró o el `JWT_SECRET` del servidor no es el mismo con que se generó. Regenera el token. |
| Puerto 8000 ocupado | `uvicorn demo.main:app --port 8010` y cambia `baseUrl`. |
| Thunder Client no carga la colección | Usa los `curl` de arriba. |
