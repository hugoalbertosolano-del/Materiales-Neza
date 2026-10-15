"""
NezaMateriales — Punto de entrada de la API REST y Servidor Web.

Arranca con: uvicorn backend.main:app --reload
"""

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.app.errors import NezaException
from backend.app.limiter import limiter
from backend.app.routers import products, quotes, whatsapp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("neza.main")

app = FastAPI(
    title="NezaMateriales API",
    description=(
        "API REST para cotización y cálculo automatizado de materiales "
        "de construcción — Nezahualcóyotl"
    ),
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# Middleware CORS
# ---------------------------------------------------------------------------
# Lista explícita de orígenes permitidos — NUNCA "*" en producción.
# ALLOWED_ORIGINS: lista separada por comas en la variable de entorno.
_default_origins = "https://neza-materiales-2026.web.app,https://neza-materiales-2026.firebaseapp.com"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------------------------------------------------------------------------
# Headers de seguridad HTTP en todas las respuestas
# ---------------------------------------------------------------------------
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


# ---------------------------------------------------------------------------
# Manejador global de excepciones personalizadas
# ---------------------------------------------------------------------------
@app.exception_handler(NezaException)
async def neza_exception_handler(_request: Request, exc: NezaException):
    """Retorna JSON consistente según convención de AGENTS.md."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.message},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Red de seguridad final: registra cualquier error no previsto (con
    traceback) para poder auditarlo, y responde un 500 genérico sin
    filtrar detalles internos al cliente.
    """
    logger.exception("Error no manejado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Error interno del servidor."},
    )


# ---------------------------------------------------------------------------
# Inclusión de Routers
# ---------------------------------------------------------------------------
app.include_router(products.router)
app.include_router(quotes.router)
app.include_router(whatsapp.router)

# ---------------------------------------------------------------------------
# Endpoint de Salud
# ---------------------------------------------------------------------------
@app.get("/health", tags=["sistema"])
async def health_check():
    """Endpoint para verificar que el servidor está activo."""
    return {"status": "ok", "service": "NezaMateriales API"}

# ---------------------------------------------------------------------------
# Archivos Estáticos (Frontend) — solo para desarrollo local.
# En producción el frontend se sirve por separado desde Firebase Hosting;
# no montamos el árbol completo si APP_ENV=production para evitar servir
# accidentalmente archivos de más desde el proceso de la API.
# ---------------------------------------------------------------------------
if os.getenv("APP_ENV", "development") != "production":
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    if frontend_dir.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
