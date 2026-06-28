import os
from typing import cast

import httpx
from typing_extensions import override

from app.providers.stt.base import BaseSTTProvider
from app.retry import retry_request


class DeepgramSTTProvider(BaseSTTProvider):
    api_key: str
    language: str

    def __init__(self) -> None:
        self.api_key = os.environ["STT_API_KEY"]
        self.language = os.environ.get("STT_LANGUAGE", os.environ.get("LANGUAGE", "en"))

    @override
    async def transcribe(self, audio_bytes: bytes) -> str:
        url = "https://api.deepgram.com/v1/listen"
        params = {"language": self.language}
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "audio/ogg",
        }
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await retry_request(lambda: client.post(
                url, params=params, headers=headers, content=audio_bytes,
            ))
            _ = response.raise_for_status()
            data = cast("dict[str, object]", response.json())
            results = cast("dict[str, object]", data["results"])
            channels = cast("list[object]", results["channels"])
            channel = cast("dict[str, object]", channels[0])
            alternatives = cast("list[object]", channel["alternatives"])
            alternative = cast("dict[str, object]", alternatives[0])
            return str(alternative["transcript"])
