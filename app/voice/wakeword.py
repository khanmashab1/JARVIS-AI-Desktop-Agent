"""Wake-word detection logic for hands-free activation."""

from typing import Callable, Optional
from app.utils.logging import get_logger

logger = get_logger("voice.wakeword")


class WakeWordDetector:
    """Detects target activation phrases like 'Hey JARVIS'."""

    def __init__(
        self,
        wake_phrase: str = "hey jarvis",
        on_wake_detected: Optional[Callable[[], None]] = None,
    ) -> None:
        self.wake_phrase = wake_phrase.strip().lower()
        self.on_wake_detected = on_wake_detected

    def check_text(self, transcribed_text: str) -> bool:
        """Evaluate if the transcription starts with or contains the wake phrase."""
        clean = transcribed_text.lower().strip()
        if self.wake_phrase in clean or clean.startswith("jarvis"):
            logger.info(f"Wake word '{self.wake_phrase}' detected in text: '{transcribed_text}'")
            if self.on_wake_detected:
                self.on_wake_detected()
            return True
        return False

    def strip_wake_word(self, text: str) -> str:
        """Remove wake phrase from the start of the command."""
        clean = text.strip()
        lower = clean.lower()
        if lower.startswith(self.wake_phrase):
            return clean[len(self.wake_phrase):].strip(" ,:.-")
        if lower.startswith("jarvis"):
            return clean[6:].strip(" ,:.-")
        return clean
