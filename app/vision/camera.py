"""OpenCV camera capture worker with non-blocking thread execution."""

import threading
import time
from typing import Callable, List, Optional
import cv2

from app.utils.logging import get_logger

logger = get_logger("vision.camera")


class CameraWorker:
    """Non-blocking camera thread reading webcam frames at throttled FPS for target PC."""

    def __init__(self, camera_index: int = 0, fps: int = 8) -> None:
        self.camera_index = camera_index
        self.fps = max(1, fps)
        self.frame_delay = 1.0 / self.fps
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._cap: Optional[cv2.VideoCapture] = None
        self._listeners: List[Callable[[Any], None]] = []

    def add_frame_listener(self, callback: Callable[[Any], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_frame_listener(self, callback: Callable[[Any], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def start(self) -> bool:
        if self._running:
            return True
        try:
            self._cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW if cv2.CAP_DSHOW else cv2.CAP_ANY)
            if not self._cap or not self._cap.isOpened():
                # Fallback standard index
                self._cap = cv2.VideoCapture(self.camera_index)
            if not self._cap.isOpened():
                logger.warning(f"Could not open webcam at index {self.camera_index}.")
                return False

            self._running = True
            self._thread = threading.Thread(target=self._capture_loop, daemon=True, name="camera-worker")
            self._thread.start()
            logger.info(f"Camera worker started on index {self.camera_index} @ {self.fps} FPS.")
            return True
        except Exception as e:
            logger.error(f"Failed to start camera: {e}")
            return False

    def stop(self) -> None:
        self._running = False
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        logger.info("Camera worker stopped.")

    def is_running(self) -> bool:
        return self._running

    def _capture_loop(self) -> None:
        while self._running and self._cap and self._cap.isOpened():
            start = time.time()
            ret, frame = self._cap.read()
            if not ret or frame is None:
                time.sleep(0.1)
                continue

            for listener in list(self._listeners):
                try:
                    listener(frame)
                except Exception as ex:
                    logger.error(f"Error in frame listener: {ex}")

            elapsed = time.time() - start
            sleep_time = max(0.01, self.frame_delay - elapsed)
            time.sleep(sleep_time)
