"""Face, eye, and presence detection using OpenCV Haar Cascades."""

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple
import cv2
import numpy as np

from app.utils.logging import get_logger

logger = get_logger("vision.face")


@dataclass
class FaceDetectionResult:
    face_count: int
    has_face: bool
    eyes_detected_count: int
    eyes_closed: bool
    bounding_boxes: List[Tuple[int, int, int, int]]


class FaceDetector:
    """Detects user presence, facial bounding boxes, and eye states."""

    def __init__(self) -> None:
        self.face_cascade = None
        self.eye_cascade = None
        self._init_cascades()

    def _init_cascades(self) -> None:
        try:
            face_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            eye_path = cv2.data.haarcascades + "haarcascade_eye.xml"
            self.face_cascade = cv2.CascadeClassifier(face_path)
            self.eye_cascade = cv2.CascadeClassifier(eye_path)
        except Exception as e:
            logger.warning(f"Could not load Haar cascades: {e}")

    def detect(self, frame: np.ndarray) -> FaceDetectionResult:
        if frame is None or self.face_cascade is None:
            return FaceDetectionResult(0, False, 0, True, [])

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Resize for speed
            small_gray = cv2.resize(gray, (0, 0), fx=0.5, fy=0.5)
            faces = self.face_cascade.detectMultiScale(small_gray, scaleFactor=1.2, minNeighbors=4, minSize=(30, 30))

            if len(faces) == 0:
                return FaceDetectionResult(0, False, 0, True, [])

            boxes = []
            total_eyes = 0

            for (x, y, w, h) in faces:
                # Scale back up
                orig_box = (x * 2, y * 2, w * 2, h * 2)
                boxes.append(orig_box)

                # Upper half of the face for eye detection
                roi_gray = small_gray[y : y + int(h * 0.6), x : x + w]
                if self.eye_cascade is not None:
                    eyes = self.eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.15, minNeighbors=3, minSize=(10, 10))
                    total_eyes += len(eyes)

            # If face is detected but zero eyes are found in upper region, likely eyes closed
            eyes_closed = (total_eyes == 0)

            return FaceDetectionResult(
                face_count=len(faces),
                has_face=True,
                eyes_detected_count=total_eyes,
                eyes_closed=eyes_closed,
                bounding_boxes=boxes,
            )
        except Exception as e:
            logger.error(f"Error in face detection: {e}")
            return FaceDetectionResult(0, False, 0, False, [])
