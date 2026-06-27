import os
from unittest.mock import patch

import httpx
import pytest

from app.providers.tts.orchardrun import OrchardRunTTSProvider

_REQUEST = httpx.Request("POST", "https://test")


@pytest.fixture
def provider() -> OrchardRunTTSProvider:
    with patch.dict(os.environ, {"ORCHARD_API_KEY": "ork-test"}, clear=True):
        return OrchardRunTTSProvider()


@pytest.mark.asyncio
async def test_synthesize_returns_bytes(provider: OrchardRunTTSProvider) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"fake ogg audio",
            request=_REQUEST,
        )

    with patch("app.providers.tts.orchardrun.retry_request", mock_retry):
        result = await provider.synthesize("hello")

    assert result == b"fake ogg audio"


@pytest.mark.asyncio
async def test_synthesize_raises_on_http_error(
    provider: OrchardRunTTSProvider,
) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            500,
            json={"error": "server error"},
            request=_REQUEST,
        )

    with (
        patch("app.providers.tts.orchardrun.retry_request", mock_retry),
        pytest.raises(httpx.HTTPStatusError),
    ):
        _ = await provider.synthesize("hello")
