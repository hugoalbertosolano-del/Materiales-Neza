"""
NezaMateriales — Webhook del bot de WhatsApp (Meta WhatsApp Cloud API).

Verifica el webhook (GET) y recibe mensajes entrantes (POST). La lógica de
conversación vive en backend/app/services/whatsapp_bot.py; este router solo
se encarga del protocolo HTTP/Meta (verificación de token/firma, envío de la
respuesta por la Graph API) para mantenerlo desacoplado y testeable.

Documentación: https://developers.facebook.com/docs/whatsapp/cloud-api
"""

import hashlib
import hmac
import logging
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.limiter import limiter
from backend.app.services.whatsapp_bot import process_incoming_message

logger = logging.getLogger("neza.whatsapp")

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v20.0")
APP_ENV = os.getenv("APP_ENV", "development")

GRAPH_API_URL = "https://graph.facebook.com/{version}/{phone_number_id}/messages"


@router.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
):
    """Verificación inicial que Meta exige al configurar la URL del webhook."""
    if not WHATSAPP_VERIFY_TOKEN:
        logger.error("WHATSAPP_VERIFY_TOKEN no configurado; se rechaza la verificación del webhook.")
        raise HTTPException(status_code=503, detail="Webhook no configurado.")

    if hub_mode == "subscribe" and hmac.compare_digest(hub_verify_token, WHATSAPP_VERIFY_TOKEN):
        return Response(content=hub_challenge, media_type="text/plain")

    raise HTTPException(status_code=403, detail="Token de verificación inválido.")


def _verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Valida X-Hub-Signature-256 contra WHATSAPP_APP_SECRET.

    En producción, si falta WHATSAPP_APP_SECRET se rechaza toda petición:
    sin secreto no hay forma de distinguir un webhook real de Meta de uno
    falsificado por un tercero. En desarrollo se permite omitir el secreto
    para poder probar el bot antes de configurar la app de Meta.
    """
    if not WHATSAPP_APP_SECRET:
        if APP_ENV == "production":
            logger.error("WHATSAPP_APP_SECRET no configurado en producción; se rechazan todos los webhooks.")
            return False
        logger.warning("WHATSAPP_APP_SECRET no configurado; se omite verificación de firma (solo desarrollo).")
        return True

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(WHATSAPP_APP_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    received = signature_header[len("sha256="):]
    return hmac.compare_digest(expected, received)


def _send_whatsapp_message(to: str, text: str) -> None:
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.error("Credenciales de WhatsApp no configuradas; no se pudo responder a %s", to)
        return

    url = GRAPH_API_URL.format(version=WHATSAPP_API_VERSION, phone_number_id=WHATSAPP_PHONE_NUMBER_ID)
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("Fallo al enviar mensaje de WhatsApp a %s", to)


@router.post("/webhook")
@limiter.limit("60/minute")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Recibe eventos entrantes de Meta (mensajes, confirmaciones de entrega, etc.).
    Siempre responde 200: Meta reintenta agresivamente si no recibe una respuesta.
    """
    raw_body = await request.body()
    if not _verify_signature(raw_body, request.headers.get("X-Hub-Signature-256")):
        logger.warning("Firma de webhook de WhatsApp inválida; se ignora la petición.")
        raise HTTPException(status_code=403, detail="Firma inválida.")

    payload = await request.json()

    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                for message in change.get("value", {}).get("messages", []):
                    phone = message.get("from")
                    text_body = (message.get("text") or {}).get("body")
                    if not phone or not text_body:
                        continue  # Ignora mensajes que no sean de texto (imágenes, audio, ubicación, etc.)

                    reply = process_incoming_message(db, phone=phone, text=text_body)
                    _send_whatsapp_message(phone, reply)
    except Exception:
        logger.exception("Error procesando webhook de WhatsApp")

    return {"status": "ok"}
