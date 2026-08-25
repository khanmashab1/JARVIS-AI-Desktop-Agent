"""Voice Speaker coordinating Text-to-Speech output."""

from typing import List, Optional
from app.providers.tts.base import TTSProvider
from app.utils.logging import get_logger

logger = get_logger("voice.speaker")


class VoiceSpeaker:
    """Manages spoken responses, rate, volume, and speech interruptions."""

    def __init__(self, tts_provider: TTSProvider, enabled: bool = True) -> None:
        self.tts = tts_provider
        self.enabled = enabled

    def speak(self, text: str, interrupt: bool = False) -> bool:
        if not self.enabled:
            return False
        return self.tts.speak(text, interrupt=interrupt)

    def stop(self) -> None:
        self.tts.stop()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if not enabled:
            self.stop()

    def get_voices(self) -> List[str]:
        return self.tts.get_available_voices()

    def set_voice(self, voice_id: str) -> None:
        self.tts.set_voice(voice_id)

    def set_rate(self, rate: int) -> None:
        self.tts.set_rate(rate)

    def set_volume(self, volume: float) -> None:
        self.tts.set_volume(volume)
