"""
NezaMateriales — Catálogo de productos: datos semilla y consulta compartida.

Usado tanto por el router REST (backend/app/routers/products.py) como por el
bot de WhatsApp (backend/app/services/whatsapp_bot.py), para no duplicar la
lógica de resiliencia (BD -> semillas de respaldo) ni los datos de catálogo.
"""

import logging
from typing import Optional

logger = logging.getLogger("neza.products_service")

# Imagen de respaldo genérica (bodega de materiales) si un producto no trae foto propia.
DEFAULT_IMAGE_URL = "/assets/img/default-fallback.jpg"

# Datos enriquecidos para la experiencia visual de NezaMateriales (fotos y rendimiento en obra).
PRODUCT_ENRICHMENT = {
    1: {
        "image_url": "/assets/img/cemento-tolteca.jpg",
        "yield_info": "1 bulto de 50 kg rinde aprox 0.16 m³ de mortero para pega de tabique (aprox 3.3 m² de muro) o 0.15 m³ de concreto estructural.",
    },
    2: {
        "image_url": "/assets/img/tabique-rojo.jpg",
        "yield_info": "Rendimiento exacto: 52 piezas por m² de muro asentado con junta de mortero de 1.5 cm.",
    },
    3: {
        "image_url": "/assets/img/varilla-3-8.jpg",
        "yield_info": "Varilla corrugada de 3/8\" (9.5 mm) de 12 m. Pesa aprox 6.72 kg por pieza. Ideal para castillos, cadenas y armado de losa.",
    },
    4: {
        "image_url": "/assets/img/arena-rio.jpg",
        "yield_info": "1 m³ de arena rinde para la mezcla de mortero de approx 45 m² de muro de tabique o 1.8 m³ de concreto f'c=150.",
    },
    5: {
        "image_url": "/assets/img/grava-triturada.jpg",
        "yield_info": "1 m³ de grava 3/4\" rinde para approx 1.6 m³ de concreto f'c=150 kg/cm² o 1.61 m³ de concreto f'c=200 kg/cm².",
    },
    6: {
        "image_url": "/assets/img/mortero-premezclado.jpg",
        "yield_info": "Mortero premezclado listo para usar: 1 bulto de 25 kg rinde aprox 0.018 m³, ideal para reparaciones y aplanados menores.",
    },
    7: {
        "image_url": "/assets/img/block-hueco.jpg",
        "yield_info": "12.5 piezas por m² de muro (junta de 1 cm). Ideal para muros de carga, bardas y cubos de escalera.",
    },
    8: {
        "image_url": "/assets/img/adoquin.jpg",
        "yield_info": "Aprox 43 piezas por m² de piso o andador, colocado sobre cama de arena de 5 cm.",
    },
    9: {
        "image_url": "/assets/img/varilla-1-2.jpg",
        "yield_info": "Varilla corrugada de 1/2\" (12.7 mm) de 12 m. Pesa aprox 11.84 kg por pieza. Uso en columnas, trabes y losas estructurales.",
    },
    10: {
        "image_url": "/assets/img/malla-electrosoldada.jpg",
        "yield_info": "Hoja de 6×2.35 m (14.1 m²). Refuerzo estándar para losas de piso y firmes de concreto sobre terreno.",
    },
    11: {
        "image_url": "/assets/img/pintura-vinilica.jpg",
        "yield_info": "1 cubeta de 19 L rinde aprox 40-45 m² por manos (2 manos) sobre muro aplanado y sellado.",
    },
    12: {
        "image_url": "/assets/img/impermeabilizante.jpg",
        "yield_info": "1 cubeta de 19 L rinde aprox 10-12 m² a dos manos sobre losa de azotea previamente limpia.",
    },
    13: {
        "image_url": "/assets/img/tubo-pvc.jpg",
        "yield_info": "Tramo de 6 m, cédula 40 para agua fría a presión. Requiere cemento solvente para unión.",
    },
    14: {
        "image_url": "/assets/img/conexion-cobre.jpg",
        "yield_info": "Conexión roscada de cobre tipo M para instalación hidráulica. Se suelda con soldadura de plata o estaño.",
    },
    15: {
        "image_url": "/assets/img/cable-electrico.jpg",
        "yield_info": "Rollo de 100 m, calibre 12 AWG, 600V. Uso en circuitos derivados de contactos e iluminación.",
    },
    16: {
        "image_url": "/assets/img/carretilla.jpg",
        "yield_info": "Capacidad de 6 pies³ (170 L). Herramienta esencial para acarreo de mezcla y escombro en obra.",
    },
    17: {
        "image_url": "/assets/img/cuchara-albanil.jpg",
        "yield_info": "Cuchara de albañil de 8\" para pega de tabique/block y aplanados finos.",
    },
    18: {
        "image_url": "/assets/img/pala-recta.jpg",
        "yield_info": "Pala recta de punta con cabo de madera, uso rudo para excavación y mezclado manual.",
    },
}

SEED_PRODUCTS = [
    {
        "id": 1,
        "name": "Cemento Tolteca 50 kg",
        "description": "Cemento Portland Compuesto CPC 30R, bulto de 50 kg. Alta resistencia inicial, ideal para losas, columnas y mampostería en Nezahualcóyotl.",
        "unit": "bulto",
        "price": 235.00,
        "category": "Cementantes",
    },
    {
        "id": 6,
        "name": "Mortero Premezclado 25 kg",
        "description": "Mortero cementante premezclado listo para usar, bulto de 25 kg. Ideal para reparaciones, resanes y aplanados menores.",
        "unit": "bulto",
        "price": 95.00,
        "category": "Cementantes",
    },
    {
        "id": 2,
        "name": "Tabique rojo 6×12×24 cm",
        "description": "Tabique rojo recocido artesanal de primera calidad para muros de carga y divisorios.",
        "unit": "pieza",
        "price": 3.50,
        "category": "Mampostería",
    },
    {
        "id": 7,
        "name": "Block hueco de concreto 15×20×40 cm",
        "description": "Block de concreto estándar para muros de carga, bardas y cubos de escalera.",
        "unit": "pieza",
        "price": 14.50,
        "category": "Mampostería",
    },
    {
        "id": 8,
        "name": "Adoquín de concreto tipo tráfico",
        "description": "Adoquín de concreto vibroprensado para pisos, andadores y cocheras.",
        "unit": "pieza",
        "price": 8.50,
        "category": "Mampostería",
    },
    {
        "id": 3,
        "name": "Varilla corrugada 3/8\" (9.5 mm)",
        "description": "Varilla de acero grado 42 tramo de 12 metros. Norma NOM-B-507.",
        "unit": "pieza",
        "price": 125.00,
        "category": "Acero",
    },
    {
        "id": 9,
        "name": "Varilla corrugada 1/2\" (12.7 mm)",
        "description": "Varilla de acero grado 42 tramo de 12 metros, para columnas, trabes y losas estructurales.",
        "unit": "pieza",
        "price": 210.00,
        "category": "Acero",
    },
    {
        "id": 10,
        "name": "Malla electrosoldada 6×6-10/10",
        "description": "Malla de refuerzo electrosoldada en hoja de 6×2.35 m para losas de piso y firmes de concreto.",
        "unit": "hoja",
        "price": 680.00,
        "category": "Acero",
    },
    {
        "id": 4,
        "name": "Arena de río",
        "description": "Arena cribada limpia de mina/río para morteros, aplanados y concretos por metro cúbico.",
        "unit": "m³",
        "price": 650.00,
        "category": "Agregados",
    },
    {
        "id": 5,
        "name": "Grava triturada 3/4\"",
        "description": "Agregado grueso triturado de 3/4 de pulgada para firme, losa y cimentación.",
        "unit": "m³",
        "price": 750.00,
        "category": "Agregados",
    },
    {
        "id": 11,
        "name": "Pintura vinílica 19 L",
        "description": "Pintura vinílica lavable para interior y exterior, cubeta de 19 litros.",
        "unit": "cubeta",
        "price": 780.00,
        "category": "Acabados",
    },
    {
        "id": 12,
        "name": "Impermeabilizante acrílico 19 L",
        "description": "Recubrimiento acrílico elastomérico para azoteas y losas, cubeta de 19 litros, garantía de 5 años.",
        "unit": "cubeta",
        "price": 890.00,
        "category": "Impermeabilizantes",
    },
    {
        "id": 13,
        "name": "Tubo PVC hidráulico 4\" cédula 40",
        "description": "Tubo de PVC hidráulico para agua fría a presión, tramo de 6 metros.",
        "unit": "tramo",
        "price": 320.00,
        "category": "Plomería",
    },
    {
        "id": 14,
        "name": "Conexión de cobre 1/2\" (coples)",
        "description": "Conexión roscada de cobre tipo M para instalaciones hidráulicas.",
        "unit": "pieza",
        "price": 45.00,
        "category": "Plomería",
    },
    {
        "id": 15,
        "name": "Cable eléctrico THW cal. 12 (rollo 100 m)",
        "description": "Cable de cobre THW calibre 12 AWG, 600V, rollo de 100 metros para circuitos derivados.",
        "unit": "rollo",
        "price": 890.00,
        "category": "Eléctrico",
    },
    {
        "id": 16,
        "name": "Carretilla de obra 6 pies³",
        "description": "Carretilla metálica de uso rudo, capacidad de 6 pies³ (170 litros), para acarreo de mezcla y escombro.",
        "unit": "pieza",
        "price": 890.00,
        "category": "Herramientas",
    },
    {
        "id": 17,
        "name": "Cuchara de albañil 8\"",
        "description": "Cuchara/llana de albañil de acero templado de 8 pulgadas, para pega de tabique/block y aplanados.",
        "unit": "pieza",
        "price": 145.00,
        "category": "Herramientas",
    },
    {
        "id": 18,
        "name": "Pala recta de punta",
        "description": "Pala recta de punta con cabo de madera, uso rudo para excavación y mezclado manual.",
        "unit": "pieza",
        "price": 210.00,
        "category": "Herramientas",
    },
]

for _p in SEED_PRODUCTS:
    _enrich = PRODUCT_ENRICHMENT.get(_p["id"], {})
    _p["image_url"] = _enrich.get("image_url", DEFAULT_IMAGE_URL)
    _p["yield_info"] = _enrich.get("yield_info", "Rendimiento según especificación de obra.")


def get_products(db, category: Optional[str] = None) -> list[dict]:
    """
    Obtiene el catálogo (BD si tiene datos, semillas de respaldo si no) como
    lista de dicts. Fuente única para el router REST y el bot de WhatsApp.
    """
    from backend.app.models import Product  # import local: evita ciclo con database/models

    try:
        query = db.query(Product)
        if category:
            query = query.filter(Product.category == category)
        db_products = query.all()

        if db_products:
            results = []
            for p in db_products:
                enrich = PRODUCT_ENRICHMENT.get(p.id, {})
                results.append({
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "unit": p.unit,
                    "price": p.price,
                    "category": p.category,
                    "image_url": enrich.get("image_url", DEFAULT_IMAGE_URL),
                    "yield_info": enrich.get("yield_info", "Rendimiento según especificación de obra."),
                })
            return results
    except Exception:
        logger.exception("Fallo al consultar productos en BD; usando semillas de respaldo")

    if category:
        return [dict(p) for p in SEED_PRODUCTS if p["category"] == category]
    return [dict(p) for p in SEED_PRODUCTS]


def get_product_by_id(db, product_id: int) -> Optional[dict]:
    """Obtiene un único producto por id (BD con respaldo de semillas)."""
    from backend.app.models import Product

    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if p:
            enrich = PRODUCT_ENRICHMENT.get(p.id, {})
            return {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "unit": p.unit,
                "price": p.price,
                "category": p.category,
                "image_url": enrich.get("image_url", DEFAULT_IMAGE_URL),
                "yield_info": enrich.get("yield_info", "Rendimiento según especificación de obra."),
            }
    except Exception:
        logger.exception("Fallo al consultar producto id=%s en BD; usando semillas de respaldo", product_id)

    for p in SEED_PRODUCTS:
        if p["id"] == product_id:
            return dict(p)
    return None


def get_categories(db) -> list[str]:
    """Lista de categorías distintas, en el orden en que aparecen en el catálogo."""
    seen: list[str] = []
    for p in get_products(db):
        if p["category"] and p["category"] not in seen:
            seen.append(p["category"])
    return seen
