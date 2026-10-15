"""
NezaMateriales — Esquemas Pydantic para el catálogo de productos.
"""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    unit: str
    price: Decimal
    category: Optional[str] = None


class ProductOut(ProductBase):
    id: int
    image_url: Optional[str] = None
    yield_info: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
