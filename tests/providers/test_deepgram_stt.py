import os
from unittest.mock import patch

import httpx
import pytest

from app.providers.stt.deepgram import DeepgramSTTProvider

_REQUEST = httpx.Request("POST", "https://test")


@pytest.fixture
def provider() -> DeepgramSTTProvider:
    with patch.dict(os.environ, {"STT_API_KEY": "dg-test"}, clear=True):
        return DeepgramSTTProvider()


@pytest.mark.asyncio
async def test_transcribe_parses_response(
    provider: DeepgramSTTProvider,
) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": {
                    "channels": [
                        {"alternatives": [{"transcript": "hola"}]},
                    ],
                },
            },
            request=_REQUEST,
        )

    with patch("app.providers.stt.deepgram.retry_request", mock_retry):
        result = await provider.transcribe(b"fake audio bytes")

    assert result == "hola"


@pytest.mark.asyncio
async def test_transcribe_raises_on_http_error(
    provider: DeepgramSTTProvider,
) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            403,
            json={"error": "forbidden"},
            request=_REQUEST,
        )

    with (
        patch("app.providers.stt.deepgram.retry_request", mock_retry),
        pytest.raises(httpx.HTTPStatusError),
    ):
        _ = await provider.transcribe(b"fake audio bytes")
