"""Platform detection and system query utilities."""

import os
import platform
import subprocess
from typing import Optional


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def get_platform_name() -> str:
    return platform.system()


def get_system_architecture() -> str:
    return platform.machine()


def get_os_version() -> str:
    if is_windows():
        return f"{platform.system()} {platform.release()} (Build {platform.version()})"
    return f"{platform.system()} {platform.release()}"


def get_volume_level() -> Optional[int]:
    """Retrieve current system master volume percentage (0-100)."""
    if not is_windows():
        return 50
    try:
        import comtypes
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        return int(round(volume.GetMasterVolumeLevelScalar() * 100))
    except Exception:
        return 50


def set_volume_level(level_percent: int) -> bool:
    """Set system master volume percentage (0-100)."""
    level_percent = max(0, min(100, level_percent))
    if not is_windows():
        return True
    try:
        import comtypes
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMasterVolumeLevelScalar(level_percent / 100.0, None)
        return True
    except Exception:
        return False
