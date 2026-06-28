import os
from typing import cast

import httpx
from typing_extensions import override

from app.providers.llm.base import BaseLLMProvider
from app.retry import retry_request


class AnthropicLLMProvider(BaseLLMProvider):
    api_key: str
    model: str
    system_prompt: str

    def __init__(self) -> None:
        self.api_key = os.environ["LLM_API_KEY"]
        self.model = os.environ.get("LLM_MODEL", "claude-3-5-haiku-latest")
        _lang = os.environ.get("LANGUAGE", "en")
        _default = (
            "You are a helpful voice assistant for a business. "
            f"Reply in {_lang}."
        )
        self.system_prompt = os.environ.get("SYSTEM_PROMPT", _default)

    @override
    async def complete(self, messages: list[dict[str, str]]) -> str:
        user_messages = [m for m in messages if m["role"] != "system"]

        body: dict[str, object] = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": user_messages,
        }
        if self.system_prompt:
            body["system"] = self.system_prompt

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await retry_request(lambda: client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
                json=body,
            ))
            _ = response.raise_for_status()
            data = cast("dict[str, object]", response.json())
            content = cast("list[object]", data["content"])
            block = cast("dict[str, object]", content[0])
            return str(block["text"])
