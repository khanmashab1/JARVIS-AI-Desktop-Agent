"""Factory for instantiating Text-to-Speech providers."""

from app.config import VoiceConfig
from app.constants import TTSProviderType
from app.providers.tts.base import TTSProvider
from app.providers.tts.piper import PiperTTS
from app.providers.tts.pyttsx3_provider import Pyttsx3TTS
from app.utils.logging import get_logger

logger = get_logger("providers.tts.factory")


def create_tts_provider(config: VoiceConfig) -> TTSProvider:
    """Create a TTS engine based on configuration, with pyttsx3 as primary local fallback."""
    provider_type = config.tts_provider.lower()

    if provider_type == TTSProviderType.PIPER.value:
        logger.info("Initializing Piper TTS provider.")
        return PiperTTS(voice_id=config.tts_voice, rate=config.tts_rate, volume=config.tts_volume)

    # Default to pyttsx3
    logger.info("Initializing Pyttsx3 TTS provider.")
    return Pyttsx3TTS(voice_id=config.tts_voice, rate=config.tts_rate, volume=config.tts_volume)
