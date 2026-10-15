"""
NezaMateriales — Router de Productos API REST.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.errors import ProductNotFoundError
from backend.app.limiter import limiter
from backend.app.schemas.products import ProductOut
from backend.app.services.products_service import get_product_by_id, get_products

router = APIRouter(prefix="/api/products", tags=["productos"])


@router.get("", response_model=List[ProductOut])
@limiter.limit("60/minute")
def list_products(
    request: Request,
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de productos del catálogo.
    Si la base de datos no está conectada o vacía, retorna las semillas con información extendida.
    """
    return [ProductOut(**p) for p in get_products(db, category=category)]


@router.get("/{product_id}", response_model=ProductOut)
@limiter.limit("60/minute")
def get_product(request: Request, product_id: int, db: Session = Depends(get_db)):
    """Obtiene el detalle de un producto específico."""
    product = get_product_by_id(db, product_id)
    if not product:
        raise ProductNotFoundError(product_id)
    return ProductOut(**product)
