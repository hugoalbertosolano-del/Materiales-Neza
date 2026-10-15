"""baseline: products, quotes, quote_items, whatsapp_sessions

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-06

Migración baseline escrita a mano para que coincida exactamente con
database/schema.sql y backend/app/models.py. No incluye las semillas de
productos (esas se cargan una sola vez con schema.sql).

Flujo recomendado:
  - Base de datos NUEVA: correr `mysql ... < database/schema.sql` (crea
    tablas + semillas) y luego `alembic stamp head` para que Alembic sepa
    que ya está en esta versión sin volver a ejecutar el DDL.
  - Cambios de esquema futuros: modificar backend/app/models.py y generar
    una migración nueva con `alembic revision --autogenerate`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(20), nullable=False, comment="pza, bulto, m³, kg, varilla"),
        sa.Column("price", sa.Numeric(10, 2), nullable=False, comment="Precio unitario en MXN"),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_products_category", "products", ["category"])

    op.create_table(
        "quotes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "folio", sa.String(36), nullable=False, unique=True,
            comment="UUID público no adivinable; usar este valor en URLs/API, nunca el id",
        ),
        sa.Column("client_name", sa.String(200), nullable=False),
        sa.Column("client_phone", sa.String(30), nullable=True),
        sa.Column("delivery_method", sa.String(30), nullable=True),
        sa.Column("delivery_address", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("total", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_quotes_client_phone", "quotes", ["client_phone"])

    op.create_table(
        "whatsapp_sessions",
        sa.Column("phone_number", sa.String(30), primary_key=True),
        sa.Column("state", sa.String(50), nullable=False, server_default="menu"),
        sa.Column("context", sa.Text(), nullable=True, comment="JSON con datos parciales del flujo actual"),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(),
            server_onupdate=sa.func.now(), nullable=False,
        ),
    )

    op.create_table(
        "quote_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("quote_id", sa.Integer(), sa.ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 4), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
    )
    op.create_index("idx_quote_items_quote", "quote_items", ["quote_id"])


def downgrade() -> None:
    op.drop_table("quote_items")
    op.drop_table("whatsapp_sessions")
    op.drop_index("idx_quotes_client_phone", table_name="quotes")
    op.drop_table("quotes")
    op.drop_index("idx_products_category", table_name="products")
    op.drop_table("products")
