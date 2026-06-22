from abc import ABC, abstractmethod


class BaseTTSProvider(ABC):
    """Abstract base for Text-to-Speech providers."""

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Convert text to speech and return audio bytes."""
        ...
