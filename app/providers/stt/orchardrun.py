import os
from io import BytesIO
from typing import cast

import httpx
from typing_extensions import override

from app.providers.stt.base import BaseSTTProvider
from app.retry import retry_request


class OrchardRunSTTProvider(BaseSTTProvider):
    api_key: str
    base_url: str
    language: str

    def __init__(self) -> None:
        self.api_key = os.environ["ORCHARD_API_KEY"]
        self.base_url = os.environ.get("ORCHARD_BASE_URL", "https://api.orchardrun.com")
        self.language = os.environ.get("STT_LANGUAGE", "es")

    @override
    async def transcribe(self, audio_bytes: bytes) -> str:
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await retry_request(lambda: client.post(
                f"{self.base_url}/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"file": ("audio.ogg", BytesIO(audio_bytes), "audio/ogg")},
                data={
                    "language": self.language,
                    "response_format": "json",
                },
            ))
            _ = response.raise_for_status()
            data = cast("dict[str, object]", response.json())
            return str(data["text"])
