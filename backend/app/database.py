"""
NezaMateriales — Conexión a MySQL con SQLAlchemy.

Lee credenciales desde variables de entorno (archivo .env).
Usa el driver pymysql (puro Python).
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Cargar .env solo en desarrollo; en producción las variables vienen del entorno.
load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development")

# ---------------------------------------------------------------------------
# Construcción de la URL de conexión
# ---------------------------------------------------------------------------
# Sin defaults inseguros: si falta DB_USER/DB_PASSWORD la app debe fallar
# explícitamente al arrancar, no conectarse como root con contraseña vacía.
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "neza_materiales")

# En Cloud Run no se puede llegar a MySQL por TCP/localhost: Cloud SQL se
# conecta vía socket Unix montado en /cloudsql/<INSTANCE_CONNECTION_NAME>.
# Si esta variable está definida, tiene prioridad sobre DB_HOST/DB_PORT.
INSTANCE_UNIX_SOCKET = os.getenv("INSTANCE_UNIX_SOCKET")

if not DB_USER or DB_PASSWORD is None:
    raise RuntimeError(
        "DB_USER y DB_PASSWORD son obligatorios (variables de entorno o .env). "
        "No se usan valores por defecto por seguridad."
    )

if INSTANCE_UNIX_SOCKET:
    DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}"
        f"?unix_socket={INSTANCE_UNIX_SOCKET}"
    )
else:
    DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

# ---------------------------------------------------------------------------
# Engine y sesión
# ---------------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # reconecta si MySQL cierra la conexión inactiva
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Base declarativa para modelos ORM
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Clase base para todos los modelos ORM de NezaMateriales."""
    pass


# ---------------------------------------------------------------------------
# Dependencia FastAPI para inyección de sesión
# ---------------------------------------------------------------------------
def get_db():
    """Genera una sesión de BD y la cierra al terminar el request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
