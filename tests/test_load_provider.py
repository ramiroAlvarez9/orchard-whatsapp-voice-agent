import importlib
import inspect
import os
from unittest.mock import MagicMock, patch

import pytest
from typing_extensions import override

from app.providers.llm.base import BaseLLMProvider
from app.providers.loader import load_provider
from app.providers.stt.base import BaseSTTProvider
from app.providers.tts.base import BaseTTSProvider


class FakeLLMProvider(BaseLLMProvider):
    @override
    async def complete(self, messages: list[dict[str, str]]) -> str:
        return "ok"


class FakeSTTProvider(BaseSTTProvider):
    @override
    async def transcribe(self, audio_bytes: bytes) -> str:
        return "hello"


class FakeTTSProvider(BaseTTSProvider):
    @override
    async def synthesize(self, text: str) -> bytes:
        return b"audio"


def test_loads_provider_by_name() -> None:
    fake_module = MagicMock(spec=object)

    def getmembers(_module: object) -> list[tuple[str, object]]:
        return [("FakeLLMProvider", FakeLLMProvider)]

    with (
        patch.object(importlib, "import_module", return_value=fake_module),
        patch.object(inspect, "getmembers", side_effect=getmembers),
        patch.dict(os.environ, {"LLM_PROVIDER": "miproveedor"}, clear=True),
    ):
        result = load_provider("llm", "LLM_PROVIDER", "openai", BaseLLMProvider)

    assert isinstance(result, BaseLLMProvider)


def test_loads_stt_provider() -> None:
    fake_module = MagicMock(spec=object)

    def getmembers(_module: object) -> list[tuple[str, object]]:
        return [("FakeSTTProvider", FakeSTTProvider)]

    with (
        patch.object(importlib, "import_module", return_value=fake_module),
        patch.object(inspect, "getmembers", side_effect=getmembers),
        patch.dict(os.environ, {"STT_PROVIDER": "miproveedor"}, clear=True),
    ):
        result = load_provider("stt", "STT_PROVIDER", "orchardrun", BaseSTTProvider)

    assert isinstance(result, BaseSTTProvider)


def test_loads_tts_provider() -> None:
    fake_module = MagicMock(spec=object)

    def getmembers(_module: object) -> list[tuple[str, object]]:
        return [("FakeTTSProvider", FakeTTSProvider)]

    with (
        patch.object(importlib, "import_module", return_value=fake_module),
        patch.object(inspect, "getmembers", side_effect=getmembers),
        patch.dict(os.environ, {"TTS_PROVIDER": "miproveedor"}, clear=True),
    ):
        result = load_provider("tts", "TTS_PROVIDER", "orchardrun", BaseTTSProvider)

    assert isinstance(result, BaseTTSProvider)


def test_unknown_provider_raises_error() -> None:
    with (
        patch.object(importlib, "import_module", side_effect=ModuleNotFoundError),
        patch.dict(os.environ, {"STT_PROVIDER": "nonexistent"}, clear=True),
        pytest.raises(ValueError, match=r"Create app/providers/stt/nonexistent\.py"),
    ):
        _ = load_provider("stt", "STT_PROVIDER", "orchardrun", BaseSTTProvider)


def test_no_subclass_raises_error() -> None:
    fake_module = MagicMock(spec=object)

    with (
        patch.object(importlib, "import_module", return_value=fake_module),
        patch.object(inspect, "getmembers", return_value=[]),
        patch.dict(os.environ, {"TTS_PROVIDER": "vacio"}, clear=True),
        pytest.raises(ValueError, match="No tts provider class found"),
    ):
        _ = load_provider("tts", "TTS_PROVIDER", "orchardrun", BaseTTSProvider)


def test_default_provider_when_env_not_set() -> None:
    fake_module = MagicMock(spec=object)

    def getmembers(_module: object) -> list[tuple[str, object]]:
        return [("FakeLLMProvider", FakeLLMProvider)]

    with (
        patch.object(importlib, "import_module", return_value=fake_module)
        as mock_import,
        patch.object(inspect, "getmembers", side_effect=getmembers),
        patch.dict(os.environ, {}, clear=True),
    ):
        result = load_provider("llm", "LLM_PROVIDER", "openai", BaseLLMProvider)

    assert isinstance(result, BaseLLMProvider)
    mock_import.assert_called_with("app.providers.llm.openai")
