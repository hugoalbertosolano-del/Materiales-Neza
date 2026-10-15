"""
NezaMateriales — Lógica de conversación del bot de WhatsApp.

Máquina de estados simple, persistida en `WhatsAppSession` (una fila por
número de teléfono) porque el proceso puede correr en varias instancias.
El router (backend/app/routers/whatsapp.py) solo se encarga del protocolo
HTTP/Meta; toda la lógica de negocio vive aquí para poder probarla sin
mockear la Graph API.

Flujo soportado:
  menu -> 1) ver catálogo por categoría (solo lectura)
       -> 2) cotizar (categoría -> producto -> cantidad -> ¿otro? -> nombre)
       -> 3) consultar mi último pedido
"""

import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.errors import ProductNotFoundError
from backend.app.models import WhatsAppSession
from backend.app.services import quotes_service
from backend.app.services.products_service import get_categories, get_products
from backend.app.services.quotes_service import QuoteItemInput

logger = logging.getLogger("neza.whatsapp_bot")

MENU_TEXT = (
    "👋 Hola, soy el asistente de *NezaMateriales* 🧱\n\n"
    "¿Qué necesitas hoy?\n"
    "1️⃣ Ver catálogo por categoría\n"
    "2️⃣ Cotizar materiales\n"
    "3️⃣ Consultar mi último pedido\n\n"
    "Responde con el número de la opción (o escribe *menu* en cualquier momento para volver aquí)."
)

_MENU_KEYWORDS = {"menu", "menú", "cancelar", "salir", "hola", "inicio"}


def process_incoming_message(db: Session, *, phone: str, text: str) -> str:
    """Procesa un mensaje entrante y devuelve el texto de respuesta, persistiendo el nuevo estado."""
    session = _get_or_create_session(db, phone)
    try:
        context = json.loads(session.context) if session.context else {}
    except (TypeError, ValueError):
        context = {}

    try:
        reply, new_state, new_context = _handle_state(db, session.state, phone, text.strip(), context)
    except Exception:
        logger.exception("Error procesando mensaje de WhatsApp phone=%s state=%s", phone, session.state)
        reply, new_state, new_context = (
            "Ocurrió un error inesperado de nuestro lado. Escribe *menu* para volver a empezar.",
            "menu",
            {},
        )

    session.state = new_state
    session.context = json.dumps(new_context)
    db.add(session)
    db.commit()
    return reply


def _get_or_create_session(db: Session, phone: str) -> WhatsAppSession:
    session = db.query(WhatsAppSession).filter(WhatsAppSession.phone_number == phone).first()
    if session is None:
        session = WhatsAppSession(phone_number=phone, state="menu", context=None)
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def _handle_state(db: Session, state: str, phone: str, text: str, context: dict):
    if text.lower() in _MENU_KEYWORDS:
        return MENU_TEXT, "menu", {}

    handler = _STATE_HANDLERS.get(state, _handle_menu)
    return handler(db, phone, text, context)


def _parse_index(text: str, length: int) -> Optional[int]:
    try:
        n = int(text.strip())
    except ValueError:
        return None
    if 1 <= n <= length:
        return n - 1
    return None


def _format_categories_message(categories: list[str], intro: str) -> str:
    lines = [intro]
    for i, category in enumerate(categories, start=1):
        lines.append(f"{i}. {category}")
    lines.append("\nEscribe el número de la categoría.")
    return "\n".join(lines)


def _format_products_message(products: list[dict], intro: str = "Materiales disponibles:") -> str:
    lines = [intro]
    for i, p in enumerate(products, start=1):
        lines.append(f"{i}. {p['name']} — ${Decimal(p['price']):.2f} MXN / {p['unit']}")
    lines.append("\nEscribe el número del material.")
    return "\n".join(lines)


def _handle_menu(db: Session, phone: str, text: str, context: dict):
    if text == "1":
        categories = get_categories(db)
        return (
            _format_categories_message(categories, "📋 Categorías disponibles:"),
            "ver_categoria",
            {"categories": categories},
        )
    if text == "2":
        categories = get_categories(db)
        return (
            _format_categories_message(categories, "🧾 Vamos a armar tu cotización.\nElige una categoría:"),
            "cot_categoria",
            {"categories": categories, "items": []},
        )
    if text == "3":
        return _handle_ultimo_pedido(db, phone)

    return MENU_TEXT, "menu", {}


def _handle_ultimo_pedido(db: Session, phone: str):
    quote = quotes_service.get_latest_quote_by_phone(db, phone)
    if not quote:
        return (
            "No encontré pedidos previos con este número. Escribe *2* para cotizar uno nuevo.",
            "menu",
            {},
        )

    lines = [f"📄 Tu último pedido (folio {quote.folio}):"]
    for item in quote.items:
        product_name = item.product.name if item.product else f"Producto #{item.product_id}"
        lines.append(f"- {item.quantity} {product_name} = ${item.subtotal:.2f}")
    lines.append(f"\nTotal: ${quote.total:.2f} MXN")
    lines.append("\nEscribe *menu* para más opciones.")
    return "\n".join(lines), "menu", {}


def _handle_ver_categoria(db: Session, phone: str, text: str, context: dict):
    categories = context.get("categories", [])
    idx = _parse_index(text, len(categories))
    if idx is None:
        return (
            "No entendí esa opción. " + _format_categories_message(categories, "Elige una categoría:"),
            "ver_categoria",
            context,
        )

    products = get_products(db, category=categories[idx])
    message = _format_products_message(products, f"📋 {categories[idx]}:") + "\n\nEscribe *menu* para volver al inicio."
    return message, "menu", {}


def _handle_cot_categoria(db: Session, phone: str, text: str, context: dict):
    categories = context.get("categories", [])
    idx = _parse_index(text, len(categories))
    if idx is None:
        return (
            "No entendí esa opción. " + _format_categories_message(categories, "Elige una categoría:"),
            "cot_categoria",
            context,
        )

    category = categories[idx]
    products = get_products(db, category=category)
    # Solo se guardan los campos serializables a JSON que el flujo necesita
    # (el precio se re-consulta desde la BD al confirmar la cotización).
    context["category"] = category
    context["products"] = [
        {"id": p["id"], "name": p["name"], "unit": p["unit"], "price": str(p["price"])}
        for p in products
    ]
    return _format_products_message(products), "cot_producto", context


def _handle_cot_producto(db: Session, phone: str, text: str, context: dict):
    products = context.get("products", [])
    idx = _parse_index(text, len(products))
    if idx is None:
        return (
            "No entendí esa opción. " + _format_products_message(products),
            "cot_producto",
            context,
        )

    product = products[idx]
    context["current_product_id"] = product["id"]
    context["current_product_name"] = product["name"]
    context["current_product_unit"] = product["unit"]
    return f"¿Cuántas *{product['unit']}* de *{product['name']}* necesitas? (solo el número)", "cot_cantidad", context


def _handle_cot_cantidad(db: Session, phone: str, text: str, context: dict):
    try:
        quantity = Decimal(text.replace(",", "."))
        if quantity <= 0 or quantity > Decimal("100000"):
            raise InvalidOperation
    except InvalidOperation:
        return "Escribe solo un número mayor a 0 (ejemplo: 10 o 2.5).", "cot_cantidad", context

    items = context.get("items", [])
    items.append({
        "product_id": context["current_product_id"],
        "quantity": str(quantity),
    })
    context["items"] = items
    for key in ("current_product_id", "current_product_name", "current_product_unit"):
        context.pop(key, None)

    return "Agregado ✅. ¿Deseas agregar otro material? Responde *sí* o *no*.", "cot_mas", context


def _handle_cot_mas(db: Session, phone: str, text: str, context: dict):
    lowered = text.lower()
    if lowered in ("si", "sí", "s", "yes"):
        categories = context.get("categories") or get_categories(db)
        context["categories"] = categories
        return (
            _format_categories_message(categories, "Elige otra categoría:"),
            "cot_categoria",
            context,
        )
    if lowered in ("no", "n"):
        if not context.get("items"):
            return "No agregaste ningún material. Escribe *menu* para empezar de nuevo.", "menu", {}
        return "Perfecto. ¿A nombre de quién hago la cotización?", "cot_nombre", context

    return "No entendí. Responde *sí* para agregar otro material o *no* para continuar.", "cot_mas", context


def _handle_cot_nombre(db: Session, phone: str, text: str, context: dict):
    name = text.strip()
    if len(name) < 2:
        return "Ese nombre es muy corto. ¿A nombre de quién hago la cotización?", "cot_nombre", context

    items_ctx = context.get("items", [])
    if not items_ctx:
        return "No hay materiales en tu cotización. Escribe *menu* para empezar de nuevo.", "menu", {}

    try:
        items_input = [
            QuoteItemInput(product_id=item["product_id"], quantity=Decimal(item["quantity"]))
            for item in items_ctx
        ]
        quote = quotes_service.create_quote(
            db,
            client_name=name[:200],
            items=items_input,
            client_phone=phone,
            delivery_method="flete_neza",
            description="Cotización generada vía bot de WhatsApp",
        )
    except ProductNotFoundError:
        return (
            "Uno de los materiales ya no está disponible. Escribe *menu* para empezar de nuevo.",
            "menu",
            {},
        )

    lines = [f"✅ ¡Listo, {name}! Tu cotización quedó registrada.", f"Folio: {quote.folio}"]
    for item in quote.items:
        product_name = item.product.name if item.product else f"Producto #{item.product_id}"
        lines.append(f"- {item.quantity} {product_name} = ${item.subtotal:.2f}")
    lines.append(f"\nTotal estimado: ${quote.total:.2f} MXN")
    lines.append("\nEn breve un asesor de NezaMateriales te contactará para confirmar entrega y forma de pago.")
    lines.append("Escribe *menu* si necesitas algo más.")
    return "\n".join(lines), "menu", {}


_STATE_HANDLERS = {
    "menu": _handle_menu,
    "ver_categoria": _handle_ver_categoria,
    "cot_categoria": _handle_cot_categoria,
    "cot_producto": _handle_cot_producto,
    "cot_cantidad": _handle_cot_cantidad,
    "cot_mas": _handle_cot_mas,
    "cot_nombre": _handle_cot_nombre,
}
