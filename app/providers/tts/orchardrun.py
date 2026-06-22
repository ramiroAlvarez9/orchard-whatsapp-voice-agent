import os

import httpx
from typing_extensions import override

from app.providers.tts.base import BaseTTSProvider
from app.retry import retry_request


class OrchardRunTTSProvider(BaseTTSProvider):
    api_key: str
    base_url: str
    voice_id: str

    def __init__(self) -> None:
        self.api_key = os.environ["ORCHARD_API_KEY"]
        self.base_url = os.environ.get("ORCHARD_BASE_URL", "https://api.orchardrun.com")
        self.voice_id = os.environ.get("TTS_VOICE_ID", "es_MX-claude")

    @override
    async def synthesize(self, text: str) -> bytes:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await retry_request(lambda: client.post(
                f"{self.base_url}/v1/tts/generate",
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={
                    "text": text,
                    "voice_id": self.voice_id,
                    "voice_type": "generic",
                },
            ))
            _ = response.raise_for_status()
            return response.content
