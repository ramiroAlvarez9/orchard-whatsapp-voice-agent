"""Send audio responses back through the Meta WhatsApp API."""

import logging
import os
from typing import cast

import httpx

from app.retry import retry_request
from app.whatsapp import META_BASE_URL

logger = logging.getLogger(__name__)


async def upload_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
    """Upload audio to Meta's media store and return the media ID."""
    access_token = os.environ["META_ACCESS_TOKEN"]
    phone_number_id = os.environ["META_PHONE_NUMBER_ID"]

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await retry_request(lambda: client.post(
            f"{META_BASE_URL}/{phone_number_id}/media",
            headers={"Authorization": f"Bearer {access_token}"},
            files={
                "file": ("response.ogg", audio_bytes, mime_type),
                "messaging_product": (None, "whatsapp"),
            },
        ))
        _ = response.raise_for_status()
        data = cast("dict[str, object]", response.json())
        return cast("str", data["id"])


async def send_audio_message(to_phone: str, media_id: str) -> dict[str, object]:
    """Send an audio message to a WhatsApp user using a previously uploaded media ID."""
    access_token = os.environ["META_ACCESS_TOKEN"]
    phone_number_id = os.environ["META_PHONE_NUMBER_ID"]

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await retry_request(lambda: client.post(
            f"{META_BASE_URL}/{phone_number_id}/messages",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "messaging_product": "whatsapp",
                "to": to_phone,
                "type": "audio",
                "audio": {"id": media_id},
            },
        ))
        _ = response.raise_for_status()
        return cast("dict[str, object]", response.json())


async def send_text_message(to_phone: str, body: str) -> dict[str, object]:
    """Send a text message to a WhatsApp user."""
    access_token = os.environ["META_ACCESS_TOKEN"]
    phone_number_id = os.environ["META_PHONE_NUMBER_ID"]

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await retry_request(lambda: client.post(
            f"{META_BASE_URL}/{phone_number_id}/messages",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "messaging_product": "whatsapp",
                "to": to_phone,
                "type": "text",
                "text": {"body": body},
            },
        ))
        _ = response.raise_for_status()
        return cast("dict[str, object]", response.json())
