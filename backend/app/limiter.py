"""
NezaMateriales — Instancia compartida de rate limiting (slowapi).

Se importa desde main.py (para registrar el middleware/handler) y desde
los routers (para decorar endpoints públicos con @limiter.limit(...)).
Mitiga abuso/spam en endpoints de escritura sin autenticación.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
