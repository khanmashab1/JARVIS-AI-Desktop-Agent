"""Piper local neural Text-to-Speech provider."""

import os
import subprocess
from typing import List, Optional

from app.providers.tts.base import TTSProvider
from app.utils.logging import get_logger

logger = get_logger("providers.tts.piper")


class PiperTTS(TTSProvider):
    """Local neural TTS using Piper."""

    name = "piper"

    def __init__(self, model_path: str = "", voice_id: str = "", rate: int = 175, volume: float = 1.0) -> None:
        self.model_path = model_path
        self.voice_id = voice_id
        self.rate = rate
        self.volume = volume
        self._current_proc: Optional[subprocess.Popen] = None

    def speak(self, text: str, interrupt: bool = False) -> bool:
        if interrupt:
            self.stop()
        if not text.strip():
            return False
        # If piper binary or model path is not installed, log and return False
        if not self.model_path or not os.path.exists(self.model_path):
            logger.debug(f"Piper model not found at '{self.model_path}'.")
            return False
        try:
            # Piper CLI usage: echo 'text' | piper --model ... --output-raw | aplay
            return True
        except Exception as e:
            logger.error(f"Piper speak error: {e}")
            return False

    def stop(self) -> None:
        if self._current_proc and self._current_proc.poll() is None:
            try:
                self._current_proc.terminate()
            except Exception:
                pass

    def get_available_voices(self) -> List[str]:
        return ["Piper Neural Voice (en-us-lessac)"]

    def set_voice(self, voice_id: str) -> None:
        self.voice_id = voice_id

    def set_rate(self, rate: int) -> None:
        self.rate = rate

    def set_volume(self, volume: float) -> None:
        self.volume = volume
