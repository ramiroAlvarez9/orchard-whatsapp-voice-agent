import os

import httpx
from typing_extensions import override

from app.providers.tts.base import BaseTTSProvider
from app.retry import retry_request


class OpenAITTSProvider(BaseTTSProvider):
    api_key: str
    voice: str
    model: str

    def __init__(self) -> None:
        self.api_key = os.environ["TTS_API_KEY"]
        self.voice = os.environ.get("TTS_VOICE", "alloy")
        self.model = os.environ.get("TTS_MODEL", "tts-1")

    @override
    async def synthesize(self, text: str) -> bytes:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await retry_request(lambda: client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "voice": self.voice,
                    "input": text,
                },
            ))
            _ = response.raise_for_status()
            return response.content
