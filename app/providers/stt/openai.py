import os
from io import BytesIO
from typing import cast

import httpx
from typing_extensions import override

from app.providers.stt.base import BaseSTTProvider
from app.retry import retry_request


class OpenAISTTProvider(BaseSTTProvider):
    api_key: str
    model: str

    def __init__(self) -> None:
        self.api_key = os.environ["STT_API_KEY"]
        self.model = os.environ.get("STT_MODEL", "whisper-1")

    @override
    async def transcribe(self, audio_bytes: bytes) -> str:
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await retry_request(lambda: client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"file": ("audio.ogg", BytesIO(audio_bytes), "audio/ogg")},
                data={"model": self.model},
            ))
            _ = response.raise_for_status()
            data = cast("dict[str, object]", response.json())
            return str(data["text"])
