import os
from unittest.mock import patch

import httpx
import pytest

from app.providers.llm.anthropic import AnthropicLLMProvider

_REQUEST = httpx.Request("POST", "https://test")


@pytest.fixture
def provider() -> AnthropicLLMProvider:
    with patch.dict(os.environ, {"LLM_API_KEY": "sk-test"}, clear=True):
        return AnthropicLLMProvider()


@pytest.mark.asyncio
async def test_complete_parses_response(provider: AnthropicLLMProvider) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            200,
            json={"content": [{"text": "Hello from Claude"}]},
            request=_REQUEST,
        )

    with patch("app.providers.llm.anthropic.retry_request", mock_retry):
        result = await provider.complete([{"role": "user", "content": "Hi"}])

    assert result == "Hello from Claude"


@pytest.mark.asyncio
async def test_complete_raises_on_http_error(provider: AnthropicLLMProvider) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": "unauthorized"},
            request=_REQUEST,
        )

    with (
        patch("app.providers.llm.anthropic.retry_request", mock_retry),
        pytest.raises(httpx.HTTPStatusError),
    ):
        _ = await provider.complete([{"role": "user", "content": "Hi"}])
