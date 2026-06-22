import os

import httpx
from typing_extensions import override

from app.providers.tts.base import BaseTTSProvider
from app.retry import retry_request


class ElevenLabsTTSProvider(BaseTTSProvider):
    api_key: str
    voice_id: str

    def __init__(self) -> None:
        self.api_key = os.environ["TTS_API_KEY"]
        self.voice_id = os.environ.get("TTS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    @override
    async def synthesize(self, text: str) -> bytes:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {"xi-api-key": self.api_key}
        json_body = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "output_format": "mp3_44100_128",
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await retry_request(
                lambda: client.post(url, headers=headers, json=json_body),
            )
            _ = response.raise_for_status()
            return response.content
