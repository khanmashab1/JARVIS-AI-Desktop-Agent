"""Base interface for Speech-to-Text providers."""

from abc import ABC, abstractmethod
from typing import Any


class STTProvider(ABC):
    """Abstract interface for transcribing audio into text."""

    name: str = "base"

    @abstractmethod
    def transcribe(self, audio_data: Any) -> str:
        """Convert recorded audio buffer/bytes into text."""
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if backend engine and dependencies are available."""
        raise NotImplementedError
