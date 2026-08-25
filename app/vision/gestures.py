"""Lightweight hand gesture and motion presence detection."""

from dataclasses import dataclass
from typing import Optional
import cv2
import numpy as np


@dataclass
class GestureResult:
    hand_detected: bool
    gesture_name: str
    confidence: float


class SimpleGestureDetector:
    """Detects simple hand gestures via skin color segmentation and contours."""

    def __init__(self) -> None:
        pass

    def detect(self, frame: np.ndarray) -> GestureResult:
        if frame is None:
            return GestureResult(False, "none", 0.0)

        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            # Skin tone range in HSV
            lower_skin = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)

            mask = cv2.inRange(hsv, lower_skin, upper_skin)
            mask = cv2.GaussianBlur(mask, (5, 5), 100)

            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                return GestureResult(False, "none", 0.0)

            max_contour = max(contours, key=lambda c: cv2.contourArea(c))
            area = cv2.contourArea(max_contour)

            if area > 10000:
                hull = cv2.convexHull(max_contour, returnPoints=False)
                defects = cv2.convexityDefects(max_contour, hull) if len(hull) > 3 else None
                count_defects = 0
                if defects is not None:
                    for i in range(defects.shape[0]):
                        s, e, f, d = defects[i, 0]
                        if d > 1000:
                            count_defects += 1

                if count_defects >= 4:
                    return GestureResult(True, "open_palm", 0.8)
                elif count_defects == 0:
                    return GestureResult(True, "fist_or_thumbs_up", 0.7)
                return GestureResult(True, "hand_active", 0.6)

            return GestureResult(False, "none", 0.0)
        except Exception:
            return GestureResult(False, "none", 0.0)
