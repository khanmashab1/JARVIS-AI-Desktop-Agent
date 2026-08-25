"""Speech-to-Text provider with faster-whisper and multi-lingual Urdu/English SpeechRecognition."""

import io
import os
import tempfile
import wave
from typing import Any, Optional
import numpy as np

from app.providers.stt.base import STTProvider
from app.utils.logging import get_logger

logger = get_logger("providers.stt.whisper")


class WhisperSTT(STTProvider):
    """Universal Speech-to-Text supporting English, Roman Urdu, and Urdu (ur-PK)."""

    name = "whisper"

    def __init__(self, model_size: str = "tiny") -> None:
        self.model_size = model_size
        self._whisper_model = None
        self._sr_recognizer = None
        self._mode = "none"
        self._init_backend()

    def _init_backend(self) -> None:
        # 1. Try faster-whisper
        try:
            from faster_whisper import WhisperModel
            self._whisper_model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            self._mode = "faster_whisper"
            logger.info(f"Loaded faster-whisper ({self.model_size}) on CPU.")
            return
        except Exception as e:
            logger.debug(f"faster-whisper not available ({e}). Using SpeechRecognition backend.")

        # 2. Try SpeechRecognition
        try:
            import speech_recognition as sr
            self._sr_recognizer = sr.Recognizer()
            self._sr_recognizer.energy_threshold = 180
            self._sr_recognizer.dynamic_energy_threshold = True
            self._sr_recognizer.pause_threshold = 0.6
            self._mode = "speech_recognition"
            logger.info("Loaded multi-lingual SpeechRecognition engine as STT backend.")
            return
        except Exception as e:
            logger.warning(f"SpeechRecognition not available ({e}).")
            self._mode = "none"

    def is_available(self) -> bool:
        return self._mode != "none"

    def transcribe(self, audio_data: Any) -> str:
        """Convert numpy audio array or raw bytes into text supporting English & Urdu."""
        if not self.is_available():
            return ""

        # 1. If using faster-whisper
        if self._mode == "faster_whisper" and self._whisper_model:
            try:
                if isinstance(audio_data, np.ndarray):
                    segments, _ = self._whisper_model.transcribe(audio_data, beam_size=1)
                    return " ".join([seg.text.strip() for seg in segments]).strip()
                if isinstance(audio_data, bytes):
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                        tf.write(audio_data)
                        tmp_path = tf.name
                    try:
                        segments, _ = self._whisper_model.transcribe(tmp_path, beam_size=1)
                        return " ".join([seg.text.strip() for seg in segments]).strip()
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
            except Exception as e:
                logger.error(f"faster-whisper transcription error: {e}")
                return ""

        # 2. If using SpeechRecognition
        if self._mode == "speech_recognition" and self._sr_recognizer:
            try:
                import speech_recognition as sr

                if isinstance(audio_data, np.ndarray):
                    if audio_data.dtype == np.float32:
                        audio_int16 = (audio_data * 32767).astype(np.int16)
                    else:
                        audio_int16 = audio_data.astype(np.int16)

                    raw_bytes = audio_int16.tobytes()
                    audio_obj = sr.AudioData(raw_bytes, sample_rate=16000, sample_width=2)
                elif isinstance(audio_data, bytes):
                    bio = io.BytesIO(audio_data)
                    with sr.AudioFile(bio) as source:
                        audio_obj = self._sr_recognizer.record(source)
                else:
                    return ""

                # Try standard / English / Roman Urdu recognition first
                try:
                    text = self._sr_recognizer.recognize_google(audio_obj)
                    if text and text.strip():
                        return text.strip()
                except sr.UnknownValueError:
                    pass

                # Fallback to Urdu (ur-PK) recognition
                try:
                    text = self._sr_recognizer.recognize_google(audio_obj, language="ur-PK")
                    if text and text.strip():
                        return text.strip()
                except Exception:
                    pass

                return ""
            except Exception as ex:
                logger.error(f"SpeechRecognition error: {ex}")
                return ""

        return ""
