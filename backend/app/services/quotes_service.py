"""
NezaMateriales — Lógica compartida para crear y consultar cotizaciones.

Usada tanto por el router REST (backend/app/routers/quotes.py) como por el
bot de WhatsApp (backend/app/routers/whatsapp.py), para no duplicar la
regla de negocio más importante: el precio SIEMPRE se toma del catálogo
en el servidor, nunca de lo que mande el cliente.
"""

import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.errors import ProductNotFoundError
from backend.app.models import Product, Quote, QuoteItem

logger = logging.getLogger("neza.quotes_service")


@dataclass
class QuoteItemInput:
    product_id: int
    quantity: Decimal


def create_quote(
    db: Session,
    *,
    client_name: str,
    items: list[QuoteItemInput],
    client_phone: str | None = None,
    delivery_method: str = "flete_neza",
    delivery_address: str | None = None,
    description: str | None = None,
) -> Quote:
    """
    Crea y persiste una cotización. Lanza ProductNotFoundError si algún
    product_id no existe. El precio de cada línea se recalcula siempre
    desde Product.price (nunca se recibe del llamador).
    """
    if not items:
        raise ValueError("La cotización debe tener al menos un ítem.")

    total_quote = Decimal("0.00")
    quote_items: list[QuoteItem] = []

    for item_in in items:
        product = db.query(Product).filter(Product.id == item_in.product_id).first()
        if not product:
            raise ProductNotFoundError(item_in.product_id)

        subtotal = (item_in.quantity * product.price).quantize(Decimal("0.01"))
        total_quote += subtotal

        quote_items.append(QuoteItem(
            product_id=product.id,
            quantity=item_in.quantity,
            unit_price=product.price,
            subtotal=subtotal,
        ))

    new_quote = Quote(
        folio=str(uuid.uuid4()),
        client_name=client_name,
        client_phone=client_phone,
        delivery_method=delivery_method,
        delivery_address=delivery_address,
        description=description,
        total=total_quote,
    )
    new_quote.items = quote_items

    db.add(new_quote)
    db.commit()
    db.refresh(new_quote)

    logger.info("Cotización creada folio=%s cliente=%r total=%s", new_quote.folio, client_name, total_quote)
    return new_quote


def get_quote_by_folio(db: Session, folio: str) -> Quote | None:
    """Busca una cotización por su folio público (UUID). Nunca por id secuencial."""
    return db.query(Quote).filter(Quote.folio == folio).first()


def get_latest_quote_by_phone(db: Session, client_phone: str) -> Quote | None:
    """Usado por el bot de WhatsApp: 'mi último pedido' para quien escribe."""
    return (
        db.query(Quote)
        .filter(Quote.client_phone == client_phone)
        .order_by(Quote.created_at.desc())
        .first()
    )
