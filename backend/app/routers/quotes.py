"""
NezaMateriales — Router para la gestión de Cotizaciones y Carrito de Compras.
"""

import logging
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.errors import ProductNotFoundError, QuoteNotFoundError
from backend.app.limiter import limiter
from backend.app.models import Product, Quote, QuoteItem
from backend.app.schemas.quotes import QuoteCreate, QuoteItemOut, QuoteOut

logger = logging.getLogger("neza.quotes")

router = APIRouter(prefix="/api/quotes", tags=["cotizaciones"])


@router.post("", response_model=QuoteOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def create_quote(request: Request, quote_data: QuoteCreate, db: Session = Depends(get_db)):
    """
    Crea y guarda una cotización/pedido a partir de los ítems del carrito.

    El precio de cada ítem SIEMPRE se toma del catálogo (Product.price) en
    el servidor, nunca de lo que envíe el cliente, para evitar manipulación
    de precios. Si algo falla al guardar, se propaga un error real: nunca
    se responde un folio "de mentira" que no exista en la base de datos.
    """
    total_quote = Decimal("0.00")
    items_to_create = []

    for item_in in quote_data.items:
        product = db.query(Product).filter(Product.id == item_in.product_id).first()
        if not product:
            raise ProductNotFoundError(item_in.product_id)

        unit_price = product.price
        subtotal = (item_in.quantity * unit_price).quantize(Decimal("0.01"))
        total_quote += subtotal

        items_to_create.append({
            "product_id": product.id,
            "product_name": product.name,
            "quantity": item_in.quantity,
            "unit_price": unit_price,
            "subtotal": subtotal,
        })

    delivery_info = f"Método entrega: {quote_data.delivery_method.value.upper()}"
    if quote_data.delivery_address:
        delivery_info += f" | Dirección: {quote_data.delivery_address}"
    if quote_data.client_phone:
        delivery_info += f" | Tel: {quote_data.client_phone}"

    full_description = quote_data.description or "Cotización web"
    full_description += f" ({delivery_info})"

    new_quote = Quote(
        folio=str(uuid.uuid4()),
        client_name=quote_data.client_name,
        description=full_description,
        total=total_quote,
    )
    db.add(new_quote)
    db.flush()

    out_items = []
    for item_dict in items_to_create:
        q_item = QuoteItem(
            quote_id=new_quote.id,
            product_id=item_dict["product_id"],
            quantity=item_dict["quantity"],
            unit_price=item_dict["unit_price"],
            subtotal=item_dict["subtotal"],
        )
        db.add(q_item)
        db.flush()

        out_items.append(QuoteItemOut(
            id=q_item.id,
            product_id=q_item.product_id,
            quantity=q_item.quantity,
            unit_price=q_item.unit_price,
            subtotal=q_item.subtotal,
            product_name=item_dict["product_name"],
        ))

    db.commit()
    logger.info("Cotización creada folio=%s cliente=%r total=%s", new_quote.folio, new_quote.client_name, total_quote)

    return QuoteOut(
        folio=new_quote.folio,
        client_name=new_quote.client_name,
        description=new_quote.description,
        total=new_quote.total,
        created_at=new_quote.created_at,
        items=out_items,
    )


@router.get("/{folio}", response_model=QuoteOut)
@limiter.limit("30/minute")
def get_quote(request: Request, folio: str, db: Session = Depends(get_db)):
    """
    Obtiene el detalle de una cotización por su folio público (UUID).

    Se busca por `folio`, nunca por el `id` interno autoincremental: así
    un folio no se puede adivinar recorriendo números consecutivos (IDOR).
    """
    quote = db.query(Quote).filter(Quote.folio == folio).first()
    if not quote:
        raise QuoteNotFoundError(folio)

    out_items = [
        QuoteItemOut(
            id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item.subtotal,
            product_name=item.product.name if item.product else f"Producto #{item.product_id}",
        )
        for item in quote.items
    ]

    return QuoteOut(
        folio=quote.folio,
        client_name=quote.client_name,
        description=quote.description,
        total=quote.total,
        created_at=quote.created_at,
        items=out_items,
    )
