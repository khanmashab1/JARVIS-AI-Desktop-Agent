"""Base interface for Text-to-Speech engines."""

from abc import ABC, abstractmethod
from typing import List, Optional


class TTSProvider(ABC):
    """Abstract interface for synthetic speech output."""

    name: str = "base"

    @abstractmethod
    def speak(self, text: str, interrupt: bool = False) -> bool:
        """Synthesize and vocalize text."""
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """Interrupt any currently playing speech."""
        raise NotImplementedError

    @abstractmethod
    def get_available_voices(self) -> List[str]:
        """Return list of voice identifiers available on the system."""
        raise NotImplementedError

    @abstractmethod
    def set_voice(self, voice_id: str) -> None:
        """Select speech voice."""
        raise NotImplementedError

    @abstractmethod
    def set_rate(self, rate: int) -> None:
        """Set speech speed rate (words per minute)."""
        raise NotImplementedError

    @abstractmethod
    def set_volume(self, volume: float) -> None:
        """Set speech volume (0.0 to 1.0)."""
        raise NotImplementedError
