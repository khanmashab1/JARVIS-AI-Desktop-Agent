"""Desktop screenshot utilities."""

from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageGrab


def capture_desktop_screenshot(save_path: Optional[str | Path] = None) -> Tuple[Image.Image, Optional[Path]]:
    """Grab the desktop screen and optionally save to disk."""
    img = ImageGrab.grab()
    saved_file: Optional[Path] = None
    if save_path:
        saved_file = Path(save_path).resolve()
        saved_file.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(saved_file))
    return img, saved_file
