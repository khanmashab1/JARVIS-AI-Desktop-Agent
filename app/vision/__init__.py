"""Computer vision, webcam monitoring, face/eye detection, and screenshot utilities."""

from app.vision.camera import CameraWorker
from app.vision.face import FaceDetector
from app.vision.gestures import SimpleGestureDetector
from app.vision.screenshot import capture_desktop_screenshot

__all__ = ["CameraWorker", "FaceDetector", "SimpleGestureDetector", "capture_desktop_screenshot"]
