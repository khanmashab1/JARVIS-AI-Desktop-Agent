"""System diagnostic, telemetry, and volume control tools."""

from datetime import datetime
import platform
from typing import Any, Dict, Optional
import psutil

from app.constants import RiskLevel
from app.tools.base import Tool, ToolResult
from app.utils.platform import get_volume_level, set_volume_level


class GetCurrentTimeTool(Tool):
    name = "get_current_time"
    description = "Returns the current local date, time, and timezone."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> ToolResult:
        now = datetime.now()
        out = {
            "datetime": now.isoformat(),
            "formatted": now.strftime("%A, %B %d, %Y at %I:%M:%S %p"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
        }
        return ToolResult(success=True, output=out)


class GetSystemInformationTool(Tool):
    name = "get_system_information"
    description = "Returns hardware, OS, CPU architecture, uptime, and host specs."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> ToolResult:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        info = {
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "cpu_cores_physical": psutil.cpu_count(logical=False),
            "cpu_cores_logical": psutil.cpu_count(logical=True),
            "total_ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
            "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return ToolResult(success=True, output=info)


class GetCpuUsageTool(Tool):
    name = "get_cpu_usage"
    description = "Returns the current overall and per-core CPU utilization percentage."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> ToolResult:
        overall = psutil.cpu_percent(interval=0.1)
        per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
        return ToolResult(success=True, output={"overall_percent": overall, "per_core_percent": per_cpu})


class GetMemoryUsageTool(Tool):
    name = "get_memory_usage"
    description = "Returns current RAM and swap memory usage statistics."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> ToolResult:
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()
        out = {
            "total_gb": round(vm.total / (1024 ** 3), 2),
            "used_gb": round(vm.used / (1024 ** 3), 2),
            "available_gb": round(vm.available / (1024 ** 3), 2),
            "percent_used": vm.percent,
            "swap_used_percent": swap.percent,
        }
        return ToolResult(success=True, output=out)


class GetDiskUsageTool(Tool):
    name = "get_disk_usage"
    description = "Returns total, used, and free disk space for a drive or partition."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Drive root or path (e.g. 'C:\\').", "default": "C:\\"},
        },
    }

    def execute(self, path: str = "C:\\", **kwargs: Any) -> ToolResult:
        try:
            usage = psutil.disk_usage(path)
            out = {
                "path": path,
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "free_gb": round(usage.free / (1024 ** 3), 2),
                "percent_used": usage.percent,
            }
            return ToolResult(success=True, output=out)
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Could not read disk usage for '{path}': {e}")


class GetBatteryStatusTool(Tool):
    name = "get_battery_status"
    description = "Returns laptop battery percentage, power plug state, and remaining discharge time."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> ToolResult:
        battery = psutil.sensors_battery()
        if not battery:
            return ToolResult(success=True, output={"status": "No battery detected (Desktop / AC powered)"})
        out = {
            "percent": battery.percent,
            "power_plugged": battery.power_plugged,
            "seconds_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Unlimited / Charging",
        }
        return ToolResult(success=True, output=out)


class GetNetworkStatusTool(Tool):
    name = "get_network_status"
    description = "Returns network interface addresses, status, and packet throughput."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> ToolResult:
        net_io = psutil.net_io_counters()
        out = {
            "bytes_sent_mb": round(net_io.bytes_sent / (1024 ** 2), 2),
            "bytes_recv_mb": round(net_io.bytes_recv / (1024 ** 2), 2),
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
        }
        return ToolResult(success=True, output=out)


class GetVolumeTool(Tool):
    name = "get_volume"
    description = "Returns the current master audio output volume (0-100)."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> ToolResult:
        vol = get_volume_level()
        return ToolResult(success=True, output={"volume_percent": vol if vol is not None else 50})


class SetVolumeTool(Tool):
    name = "set_volume"
    description = "Sets the master audio output volume (0-100)."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "level": {"type": "integer", "description": "Volume percentage from 0 to 100."},
        },
        "required": ["level"],
    }

    def execute(self, level: int, **kwargs: Any) -> ToolResult:
        level = max(0, min(100, level))
        ok = set_volume_level(level)
        if ok:
            return ToolResult(success=True, output=f"Volume set to {level}%.")
        return ToolResult(success=False, output="", error="Failed to set audio volume.")
