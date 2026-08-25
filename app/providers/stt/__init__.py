"""Speech-to-Text provider abstraction and implementations."""

from app.providers.stt.base import STTProvider
from app.providers.stt.whisper import WhisperSTT

__all__ = ["STTProvider", "WhisperSTT"]
