import os
from unittest.mock import patch

import httpx
import pytest

from app.providers.stt.openai import OpenAISTTProvider

_REQUEST = httpx.Request("POST", "https://test")


@pytest.fixture
def provider() -> OpenAISTTProvider:
    with patch.dict(os.environ, {"STT_API_KEY": "sk-test"}, clear=True):
        return OpenAISTTProvider()


@pytest.mark.asyncio
async def test_transcribe_parses_response(provider: OpenAISTTProvider) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            200,
            json={"text": "hello world"},
            request=_REQUEST,
        )

    with patch("app.providers.stt.openai.retry_request", mock_retry):
        result = await provider.transcribe(b"fake audio bytes")

    assert result == "hello world"


@pytest.mark.asyncio
async def test_transcribe_raises_on_http_error(provider: OpenAISTTProvider) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            429,
            json={"error": "rate limited"},
            request=_REQUEST,
        )

    with (
        patch("app.providers.stt.openai.retry_request", mock_retry),
        pytest.raises(httpx.HTTPStatusError),
    ):
        _ = await provider.transcribe(b"fake audio bytes")
