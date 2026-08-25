"""System Telemetry and Management Plugin for JARVIS."""

from typing import Any, Dict, List, Optional

from app.plugins.base import JarvisPlugin
from app.tools.base import Tool
from app.tools.system import (
    GetBatteryStatusTool,
    GetCpuUsageTool,
    GetDiskUsageTool,
    GetMemoryUsageTool,
    GetNetworkStatusTool,
    GetSystemInformationTool,
    GetVolumeTool,
    SetVolumeTool,
)


class SystemPlugin(JarvisPlugin):
    """System Plugin exposing real-time hardware telemetry and volume tools."""

    name = "system_manager"
    version = "1.0.0"
    description = "Provides CPU, memory, disk, battery, and hardware metrics monitoring."
    author = "JARVIS"

    def register_tools(self) -> List[Tool]:
        return [
            GetSystemInformationTool(),
            GetCpuUsageTool(),
            GetMemoryUsageTool(),
            GetDiskUsageTool(),
            GetBatteryStatusTool(),
            GetNetworkStatusTool(),
            GetVolumeTool(),
            SetVolumeTool(),
        ]
