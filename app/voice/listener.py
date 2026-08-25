"""Audio listener with adaptive Voice Activity Detection and echo isolation."""

import queue
import threading
import time
from typing import Callable, Optional
import numpy as np

from app.providers.stt.base import STTProvider
from app.utils.logging import get_logger

logger = get_logger("voice.listener")


class AudioListener:
    """Listens to microphone with adaptive noise calibration, audio gain, and echo isolation."""

    def __init__(
        self,
        stt_provider: STTProvider,
        sample_rate: int = 16000,
        energy_threshold: float = 0.008,
        silence_limit_seconds: float = 0.85,
        on_transcription: Optional[Callable[[str], None]] = None,
        on_listening_state: Optional[Callable[[bool], None]] = None,
        is_speaking_check: Optional[Callable[[], bool]] = None,
        on_barge_in: Optional[Callable[[], None]] = None,
    ) -> None:
        self.stt = stt_provider
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.silence_limit_seconds = silence_limit_seconds
        self.on_transcription = on_transcription
        self.on_listening_state = on_listening_state
        self.is_speaking_check = is_speaking_check
        self.on_barge_in = on_barge_in

        self._running = False
        self._listening = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start background microphone monitoring."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True, name="mic-listener")
        self._thread.start()
        logger.info("Adaptive audio listener worker started.")

    def stop(self) -> None:
        self._running = False
        self._set_listening_state(False)

    def is_listening(self) -> bool:
        return self._listening

    def _set_listening_state(self, state: bool) -> None:
        if self._listening != state:
            self._listening = state
            if self.on_listening_state:
                try:
                    self.on_listening_state(state)
                except Exception:
                    pass

    def _listen_loop(self) -> None:
        try:
            import sounddevice as sd
        except ImportError:
            logger.warning("sounddevice not available. Voice input disabled.")
            return

        audio_buffer = []
        is_speaking = False
        last_speech_time = time.time()

        def audio_callback(indata, frames, time_info, status):
            nonlocal is_speaking, last_speech_time
            if not self._running:
                return

            # Check if JARVIS is currently speaking through the speakers
            jarvis_is_speaking = self.is_speaking_check and self.is_speaking_check()

            if jarvis_is_speaking:
                # Discard speaker echo so JARVIS never interrupts its own speech
                if is_speaking:
                    is_speaking = False
                    audio_buffer.clear()
                    self._set_listening_state(False)
                return

            # Calculate RMS energy
            volume_norm = float(np.linalg.norm(indata) / np.sqrt(len(indata)))

            if volume_norm > self.energy_threshold:
                if not is_speaking:
                    is_speaking = True
                    self._set_listening_state(True)
                last_speech_time = time.time()
                audio_buffer.append(indata.copy())
            elif is_speaking:
                audio_buffer.append(indata.copy())

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                callback=audio_callback,
                blocksize=int(self.sample_rate * 0.1),
            ):
                while self._running:
                    time.sleep(0.08)
                    # Check silence cutoff
                    if is_speaking and (time.time() - last_speech_time > self.silence_limit_seconds):
                        is_speaking = False
                        self._set_listening_state(False)

                        if audio_buffer:
                            full_audio = np.concatenate(audio_buffer, axis=0).flatten()
                            audio_buffer.clear()

                            # Only process if we collected at least ~0.35s of audio and JARVIS is not speaking
                            if len(full_audio) >= int(self.sample_rate * 0.35):
                                if not (self.is_speaking_check and self.is_speaking_check()):
                                    # Normalize & Boost signal
                                    max_val = np.max(np.abs(full_audio))
                                    if max_val > 0.001:
                                        boosted_audio = full_audio / max_val * 0.85
                                    else:
                                        boosted_audio = full_audio

                                    text = self.stt.transcribe(boosted_audio)
                                    if text and text.strip() and self.on_transcription:
                                        logger.info(f"Transcribed speech utterance: '{text}'")
                                        self.on_transcription(text.strip())
        except Exception as e:
            logger.error(f"Error in sounddevice listener loop: {e}")
            self._set_listening_state(False)
