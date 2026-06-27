import os
from unittest.mock import patch

import httpx
import pytest

from app.providers.tts.elevenlabs import ElevenLabsTTSProvider

_REQUEST = httpx.Request("POST", "https://test")


@pytest.fixture
def provider() -> ElevenLabsTTSProvider:
    with patch.dict(os.environ, {"TTS_API_KEY": "el-test"}, clear=True):
        return ElevenLabsTTSProvider()


@pytest.mark.asyncio
async def test_synthesize_returns_bytes(provider: ElevenLabsTTSProvider) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"fake mp3 audio",
            request=_REQUEST,
        )

    with patch("app.providers.tts.elevenlabs.retry_request", mock_retry):
        result = await provider.synthesize("hello")

    assert result == b"fake mp3 audio"


@pytest.mark.asyncio
async def test_synthesize_raises_on_http_error(
    provider: ElevenLabsTTSProvider,
) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": "unauthorized"},
            request=_REQUEST,
        )

    with (
        patch("app.providers.tts.elevenlabs.retry_request", mock_retry),
        pytest.raises(httpx.HTTPStatusError),
    ):
        _ = await provider.synthesize("hello")
