"""
NezaMateriales — Esquemas Pydantic para cotizaciones y pedidos.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DeliveryMethod(str, Enum):
    """Métodos de entrega soportados. Rechaza cualquier otro valor."""
    FLETE_NEZA = "flete_neza"
    RECOLECCION = "recoleccion"


class QuoteItemCreate(BaseModel):
    product_id: int
    quantity: Decimal = Field(..., gt=0, le=100000)
    # unit_price NO se acepta del cliente: el precio real siempre se
    # recalcula en el servidor a partir de Product.price (ver quotes.py).
    # Mantenerlo así previene manipulación de precios (price tampering).


class QuoteCreate(BaseModel):
    client_name: str = Field(..., min_length=2, max_length=200)
    client_phone: Optional[str] = Field(default=None, max_length=30)
    delivery_method: DeliveryMethod = Field(default=DeliveryMethod.FLETE_NEZA)
    delivery_address: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None, max_length=500)
    items: List[QuoteItemCreate] = Field(..., min_length=1, max_length=100)


class QuoteItemOut(BaseModel):
    id: int
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal
    product_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class QuoteOut(BaseModel):
    folio: str
    client_name: str
    description: Optional[str] = None
    total: Decimal
    created_at: datetime
    items: List[QuoteItemOut]

    model_config = ConfigDict(from_attributes=True)
