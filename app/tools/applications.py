"""Application management tools for Windows desktop."""

import os
import shutil
import subprocess
from typing import Any, Dict, List
import psutil

from app.constants import RiskLevel
from app.tools.base import Tool, ToolResult
from app.utils.logging import get_logger

logger = get_logger("tools.applications")

# Known application shortcuts and common executable mappings on Windows
APP_MAPPINGS = {
    "notepad": "notepad.exe",
    "the notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "vs code": "code",
    "the vs code": "code",
    "the vscode": "code",
    "vscode": "code",
    "code": "code",
    "visual studio code": "code",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "browser": "msedge.exe",
    "spotify": "spotify.exe",
    "cmd": "cmd.exe",
    "terminal": "wt.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "paint": "mspaint.exe",
}


class OpenApplicationTool(Tool):
    name = "open_application"
    description = "Launches a desktop application by name (e.g. 'Notepad', 'VS Code', 'Calculator', 'Chrome')."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "Name or executable name of the application to launch.",
            }
        },
        "required": ["app_name"],
    }

    def execute(self, app_name: str, **kwargs: Any) -> ToolResult:
        clean_name = app_name.strip().lower().replace("open ", "").replace("launch ", "").replace("start ", "").strip()
        target_exec = APP_MAPPINGS.get(clean_name, clean_name)

        try:
            # Check if command is in PATH or directly executable
            exec_path = shutil.which(target_exec)
            if exec_path:
                subprocess.Popen([exec_path], shell=False)
                return ToolResult(success=True, output=f"Successfully launched {app_name} ({exec_path}).")

            # Check common Windows paths for VS Code if 'code' wasn't in PATH
            if "code" in target_exec or "vs" in target_exec:
                local_app_data = os.environ.get("LOCALAPPDATA", "")
                vscode_path = os.path.join(local_app_data, "Programs", "Microsoft VS Code", "Code.exe")
                if os.path.exists(vscode_path):
                    subprocess.Popen([vscode_path], shell=False)
                    return ToolResult(success=True, output=f"Successfully launched Visual Studio Code.")

            # Try start command for Windows registered apps
            if os.name == "nt":
                try:
                    os.startfile(target_exec)
                    return ToolResult(success=True, output=f"Successfully started application '{app_name}'.")
                except Exception:
                    subprocess.Popen(f'start "" "{target_exec}"', shell=True)
                    return ToolResult(success=True, output=f"Issued start request for '{app_name}'.")

            return ToolResult(success=False, output="", error=f"Application '{app_name}' not found on system.")
        except Exception as e:
            logger.error(f"Failed to open application {app_name}: {e}")
            return ToolResult(success=False, output="", error=f"Could not open '{app_name}': {e}")


class CloseApplicationTool(Tool):
    name = "close_application"
    description = "Terminates a running application by process or window name."
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "Name of the application or process to terminate (e.g. 'notepad', 'chrome').",
            }
        },
        "required": ["app_name"],
    }

    def execute(self, app_name: str, **kwargs: Any) -> ToolResult:
        clean_name = app_name.strip().lower()
        target_exec = APP_MAPPINGS.get(clean_name, clean_name).replace(".exe", "")
        terminated_count = 0

        for proc in psutil.process_iter(["pid", "name"]):
            try:
                pname = proc.info["name"].lower()
                if clean_name in pname or target_exec in pname:
                    proc.terminate()
                    terminated_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if terminated_count > 0:
            return ToolResult(success=True, output=f"Closed {terminated_count} process instance(s) matching '{app_name}'.")
        return ToolResult(success=False, output="", error=f"No active processes found matching '{app_name}'.")


class ListRunningApplicationsTool(Tool):
    name = "list_running_applications"
    description = "Returns a list of actively running desktop window applications and key processes."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of applications to list (default 25).",
                "default": 25,
            }
        },
    }

    def execute(self, limit: int = 25, **kwargs: Any) -> ToolResult:
        apps = []
        try:
            import pygetwindow as gw
            windows = gw.getAllTitles()
            visible_windows = [w.strip() for w in windows if w.strip() and w.strip() != "Program Manager"]
            if visible_windows:
                return ToolResult(success=True, output=visible_windows[:limit])
        except Exception:
            pass

        seen = set()
        for proc in psutil.process_iter(["name", "memory_percent"]):
            try:
                name = proc.info["name"]
                if name and name.endswith(".exe") and name not in seen:
                    seen.add(name)
                    apps.append(name)
            except Exception:
                continue

        return ToolResult(success=True, output=apps[:limit])


class FocusApplicationTool(Tool):
    name = "focus_application"
    description = "Brings an open application window to the foreground."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "window_title": {
                "type": "string",
                "description": "Title or partial name of the window to bring to the front.",
            }
        },
        "required": ["window_title"],
    }

    def execute(self, window_title: str, **kwargs: Any) -> ToolResult:
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(window_title)
            if not windows:
                return ToolResult(success=False, output="", error=f"No window found with title matching '{window_title}'.")
            target = windows[0]
            if target.isMinimized:
                target.restore()
            target.activate()
            return ToolResult(success=True, output=f"Brought window '{target.title}' to foreground.")
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Could not focus window '{window_title}': {e}")
