import os
from unittest.mock import patch

import httpx
import pytest

from app.providers.llm.openai import OpenAILLMProvider

_REQUEST = httpx.Request("POST", "https://test")


@pytest.fixture
def provider() -> OpenAILLMProvider:
    with patch.dict(os.environ, {"LLM_API_KEY": "sk-test"}, clear=True):
        return OpenAILLMProvider()


@pytest.mark.asyncio
async def test_complete_parses_response(provider: OpenAILLMProvider) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Hello from OpenAI"}}],
            },
            request=_REQUEST,
        )

    with patch("app.providers.llm.openai.retry_request", mock_retry):
        result = await provider.complete([{"role": "user", "content": "Hi"}])

    assert result == "Hello from OpenAI"


@pytest.mark.asyncio
async def test_complete_raises_on_http_error(provider: OpenAILLMProvider) -> None:
    async def mock_retry(_request: object) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": "unauthorized"},
            request=_REQUEST,
        )

    with (
        patch("app.providers.llm.openai.retry_request", mock_retry),
        pytest.raises(httpx.HTTPStatusError),
    ):
        _ = await provider.complete([{"role": "user", "content": "Hi"}])
