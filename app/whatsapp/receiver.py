"""Parse incoming Meta WhatsApp webhook payloads and download audio files."""

import hashlib
import hmac
import logging
import os
from typing import cast

import httpx

from app.retry import retry_request
from app.whatsapp import META_BASE_URL

logger = logging.getLogger(__name__)


def verify_signature(payload: bytes, signature_header: str, app_secret: str) -> bool:
    scheme, _, signature = signature_header.partition("=")
    if scheme != "sha256" or not signature:
        return False
    expected = hmac.new(
        app_secret.encode(), payload, hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


class WebhookPayload:
    """Parse and validate an incoming Meta webhook payload for audio messages."""

    raw: dict[str, object]

    def __init__(self, data: dict[str, object]) -> None:
        """Initialize the payload parser and immediately parse the data."""
        self.raw = data
        self.sender_phone: str = ""
        self.media_id: str = ""
        self.audio_mime_type: str = ""
        self.phone_number_id: str = ""
        self._parse()

    def _parse(self) -> None:
        try:
            entry_list = cast("list[dict[str, object]]", self.raw["entry"])
            entry = entry_list[0]
            changes = cast("list[dict[str, object]]", entry["changes"])
            change = changes[0]
            value = cast("dict[str, object]", change["value"])
            messages = cast("list[dict[str, object]]", value["messages"])
            message = messages[0]

            if message.get("type") != "audio":
                msg = "Received non-audio message"
                raise ValueError(msg)

            metadata = cast("dict[str, object]", value["metadata"])
            self.phone_number_id = cast("str", metadata["phone_number_id"])
            self.sender_phone = cast("str", message["from"])
            audio = cast("dict[str, object]", message["audio"])
            self.media_id = cast("str", audio["id"])
            self.audio_mime_type = cast(
                "str", audio.get("mime_type", "audio/ogg"),
            )
        except (KeyError, IndexError) as e:
            msg = f"Invalid webhook payload: {e}"
            raise ValueError(msg) from e


async def download_audio(media_id: str) -> bytes:
    """Download an audio file from Meta's servers using the media ID."""
    access_token = os.environ["META_ACCESS_TOKEN"]

    async with httpx.AsyncClient(timeout=60.0) as client:
        url_response = await retry_request(lambda: client.get(
            f"{META_BASE_URL}/{media_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        ))
        _ = url_response.raise_for_status()
        url_data = cast("dict[str, object]", url_response.json())
        audio_url = str(url_data["url"])

        audio_response = await retry_request(lambda: client.get(
            audio_url,
            headers={"Authorization": f"Bearer {access_token}"},
        ))
        _ = audio_response.raise_for_status()
        return audio_response.content
