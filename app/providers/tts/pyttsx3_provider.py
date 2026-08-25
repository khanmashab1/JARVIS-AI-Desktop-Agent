"""High-Fidelity Neural Edge-TTS engine with Pygame playback for human-quality Urdu and English."""

import asyncio
import os
import queue
import re
import tempfile
import threading
import time
from typing import List, Optional
import pygame

from app.providers.tts.base import TTSProvider
from app.utils.logging import get_logger

logger = get_logger("providers.tts.neural")


class Pyttsx3TTS(TTSProvider):
    """Neural Edge-TTS + Pygame audio provider supporting natural human-quality Urdu and English."""

    name = "neural_pygame"

    def __init__(self, voice_id: str = "", rate: int = 175, volume: float = 1.0) -> None:
        self.voice_id = voice_id or "ur-PK-AsadNeural"
        self.rate = rate
        self.volume = max(0.0, min(1.0, volume))
        self._speech_queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._is_speaking = False
        self._worker_thread: Optional[threading.Thread] = None

        self._init_audio_system()
        self._init_worker()

    def _init_audio_system(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=24000, size=-16, channels=2, buffer=512)
            pygame.mixer.music.set_volume(self.volume)
            logger.info("Pygame audio mixer initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Pygame mixer: {e}")

    def _init_worker(self) -> None:
        self._worker_thread = threading.Thread(target=self._run_loop, daemon=True, name="neural-tts-worker")
        self._worker_thread.start()

    def is_speaking(self) -> bool:
        return self._is_speaking

    def _detect_language(self, text: str) -> str:
        """Detect whether text is Urdu/Roman Urdu or English."""
        # 1. Arabic/Urdu unicode characters
        if re.search(r"[\u0600-\u06FF\u0750-\u077F]", text):
            return "ur-PK-AsadNeural"

        # 2. Common Roman Urdu words
        roman_urdu_words = {
            "aaj", "mausam", "kaisa", "kya", "hai", "hain", "bohot", "acha", "achi",
            "garmi", "sardi", "baarish", "dhoop", "janab", "khol", "kholo", "diya",
            "shukriya", "waqt", "time", "kitna", "kitni", "mera", "meri", "aap", "tum",
            "suvidha", "haal", "kaun", "kahan", "kab", "kyun", "walaikum", "salam"
        }
        words = set(re.findall(r"\b\w+\b", text.lower()))
        if len(words.intersection(roman_urdu_words)) >= 1:
            return "ur-PK-AsadNeural"

        return "en-US-ChristopherNeural"

    def _clean_for_speech(self, text: str) -> str:
        """Strip markdown code blocks, URLs, and asterisks for smooth speech."""
        cleaned = re.sub(r"```[\s\S]*?```", " Code block. ", text)
        cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
        cleaned = re.sub(r"[#*_~>]+", "", cleaned)
        cleaned = re.sub(r"https?://\S+", "", cleaned)
        cleaned = " ".join(cleaned.split())
        return cleaned.strip()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                raw_text = self._speech_queue.get(timeout=0.2)
                if raw_text is None:
                    break

                speech_text = self._clean_for_speech(raw_text)
                if speech_text:
                    self._is_speaking = True
                    voice_choice = self._detect_language(speech_text)
                    logger.info(f"Speaking Neural Voice ({voice_choice}): '{speech_text[:70]}...'")

                    tmp_path = None
                    try:
                        import edge_tts

                        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
                            tmp_path = tf.name

                        async def generate():
                            comm = edge_tts.Communicate(speech_text, voice_choice, rate="+15%")
                            await comm.save(tmp_path)

                        asyncio.run(generate())

                        # Play via Pygame mixer
                        if pygame.mixer.get_init():
                            pygame.mixer.music.load(tmp_path)
                            pygame.mixer.music.play()
                            while pygame.mixer.music.get_busy() and not self._stop_event.is_set() and self._is_speaking:
                                time.sleep(0.05)
                            pygame.mixer.music.stop()
                            pygame.mixer.music.unload()
                    except Exception as err:
                        logger.error(f"Neural speech error: {err}")
                    finally:
                        if tmp_path and os.path.exists(tmp_path):
                            try:
                                os.remove(tmp_path)
                            except Exception:
                                pass
                        self._is_speaking = False

                self._speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception as ex:
                logger.error(f"Error in TTS worker: {ex}")
                self._is_speaking = False

    def speak(self, text: str, interrupt: bool = False) -> bool:
        if not text or not text.strip():
            return False
        if interrupt:
            self.stop()
        self._speech_queue.put(text.strip())
        return True

    def stop(self) -> None:
        """Clear queue and immediately stop active audio playback."""
        while not self._speech_queue.empty():
            try:
                self._speech_queue.get_nowait()
                self._speech_queue.task_done()
            except Exception:
                break

        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
        except Exception:
            pass

        self._is_speaking = False
        logger.info("Audio playback halted.")

    def get_available_voices(self) -> List[str]:
        return [
            "ur-PK-AsadNeural (Urdu Male)",
            "ur-PK-UzmaNeural (Urdu Female)",
            "en-US-ChristopherNeural (English Male)",
            "en-US-GuyNeural (English Male)",
        ]

    def set_voice(self, voice_id: str) -> None:
        self.voice_id = voice_id

    def set_rate(self, rate: int) -> None:
        self.rate = rate

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self.volume)
