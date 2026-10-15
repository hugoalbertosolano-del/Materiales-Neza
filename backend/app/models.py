"""
NezaMateriales — Modelos ORM de SQLAlchemy.

Tablas: products, quotes, quote_items.
Relaciones:
  - Quote  1 ↔ N  QuoteItem
  - Product 1 ↔ N  QuoteItem
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class Product(Base):
    """Producto del catálogo de materiales de construcción."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="pza, bulto, m³, kg, varilla"
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment="Precio unitario en MXN"
    )
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relación inversa: productos referenciados en cotizaciones
    quote_items: Mapped[list["QuoteItem"]] = relationship(
        back_populates="product"
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"


class Quote(Base):
    """Cotización generada para un cliente."""

    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    folio: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True,
        comment="UUID público no adivinable; usar este valor en URLs/API, nunca el id",
    )
    client_name: Mapped[str] = mapped_column(String(200), nullable=False)
    client_phone: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    delivery_method: Mapped[str | None] = mapped_column(String(30), nullable=True)
    delivery_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relación 1:N con los ítems de la cotización
    items: Mapped[list["QuoteItem"]] = relationship(
        back_populates="quote", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Quote(id={self.id}, client='{self.client_name}', total={self.total})>"


class QuoteItem(Base):
    """Línea individual dentro de una cotización."""

    __tablename__ = "quote_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quote_id: Mapped[int] = mapped_column(
        ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Relaciones bidireccionales
    quote: Mapped["Quote"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="quote_items")

    def __repr__(self) -> str:
        return (
            f"<QuoteItem(id={self.id}, product_id={self.product_id}, "
            f"qty={self.quantity})>"
        )


class WhatsAppSession(Base):
    """
    Estado de conversación del bot de WhatsApp por número de teléfono.

    Necesario porque el proceso del backend puede correr en varias
    instancias (Cloud Run escala horizontalmente): el estado no puede
    vivir solo en memoria, se persiste aquí.
    """

    __tablename__ = "whatsapp_sessions"

    phone_number: Mapped[str] = mapped_column(String(30), primary_key=True)
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="menu")
    context: Mapped[str | None] = mapped_column(Text, nullable=True, comment="JSON con datos parciales del flujo actual")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<WhatsAppSession(phone={self.phone_number}, state={self.state})>"
