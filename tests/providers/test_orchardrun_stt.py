import os
from unittest.mock import patch

import httpx
import pytest

from app.providers.stt.orchardrun import OrchardRunSTTProvider

_REQUEST = httpx.Request("POST", "https://test")


@pytest.fixture
def provider() -> OrchardRunSTTProvider:
    with patch.dict(os.environ, {"ORCHARD_API_KEY": "ork-test"}, clear=True):
        return OrchardRunSTTProvider()


@pytest.mark.asyncio
async def test_transcribe_parses_response(provider: OrchardRunSTTProvider) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            200,
            json={"text": "hola mundo"},
            request=_REQUEST,
        )

    with patch("app.providers.stt.orchardrun.retry_request", mock_retry):
        result = await provider.transcribe(b"fake audio bytes")

    assert result == "hola mundo"


@pytest.mark.asyncio
async def test_transcribe_raises_on_http_error(provider: OrchardRunSTTProvider) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            500,
            json={"error": "server error"},
            request=_REQUEST,
        )

    with (
        patch("app.providers.stt.orchardrun.retry_request", mock_retry),
        pytest.raises(httpx.HTTPStatusError),
    ):
        _ = await provider.transcribe(b"fake audio bytes")
