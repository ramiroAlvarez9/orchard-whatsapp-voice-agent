from abc import ABC, abstractmethod


class BaseSTTProvider(ABC):
    """Abstract base for Speech-to-Text providers."""

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio bytes into text."""
        ...
