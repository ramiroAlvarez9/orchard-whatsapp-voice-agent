import os
from unittest.mock import patch

import httpx
import pytest

from app.providers.tts.openai import OpenAITTSProvider

_REQUEST = httpx.Request("POST", "https://test")


@pytest.fixture
def provider() -> OpenAITTSProvider:
    with patch.dict(os.environ, {"TTS_API_KEY": "sk-test"}, clear=True):
        return OpenAITTSProvider()


@pytest.mark.asyncio
async def test_synthesize_returns_bytes(provider: OpenAITTSProvider) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"fake mp3 audio",
            request=_REQUEST,
        )

    with patch("app.providers.tts.openai.retry_request", mock_retry):
        result = await provider.synthesize("hello")

    assert result == b"fake mp3 audio"


@pytest.mark.asyncio
async def test_synthesize_raises_on_http_error(
    provider: OpenAITTSProvider,
) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            429,
            json={"error": "rate limited"},
            request=_REQUEST,
        )

    with (
        patch("app.providers.tts.openai.retry_request", mock_retry),
        pytest.raises(httpx.HTTPStatusError),
    ):
        _ = await provider.synthesize("hello")
