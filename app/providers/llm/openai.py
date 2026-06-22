import os
from typing import cast

import httpx
from typing_extensions import override

from app.providers.llm.base import BaseLLMProvider
from app.retry import retry_request


class OpenAILLMProvider(BaseLLMProvider):
    api_key: str
    base_url: str
    model: str
    system_prompt: str

    def __init__(self) -> None:
        self.api_key = os.environ["LLM_API_KEY"]
        self.base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
        self.model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
        self.system_prompt = os.environ.get(
            "SYSTEM_PROMPT", "You are a helpful voice assistant for a business.",
        )

    @override
    async def complete(self, messages: list[dict[str, str]]) -> str:
        full_messages = [
            {"role": "system", "content": self.system_prompt},
            *messages,
        ]
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await retry_request(lambda: client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": full_messages},
            ))
            _ = response.raise_for_status()
            data = cast("dict[str, object]", response.json())
            choices = cast("list[object]", data["choices"])
            choice = cast("dict[str, object]", choices[0])
            message = cast("dict[str, object]", choice["message"])
            return str(message["content"])
