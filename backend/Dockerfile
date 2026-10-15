# NezaMateriales — Imagen del backend para Google Cloud Run.
#
# Build (desde la raíz del repo, para que el contexto incluya requirements.txt
# y el paquete backend/ completo con sus imports `backend.app.*`):
#   docker build -f backend/Dockerfile -t neza-backend-api .

FROM python:3.11-slim

WORKDIR /srv

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend

ENV APP_ENV=production \
    PYTHONUNBUFFERED=1

# Cloud Run inyecta $PORT en tiempo de ejecución (por defecto 8080).
CMD exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}
