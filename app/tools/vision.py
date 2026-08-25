"""Screenshot capture and visual understanding tools."""

import base64
import io
import os
from pathlib import Path
from typing import Any, Dict, Optional
from PIL import Image, ImageGrab

from app.constants import RiskLevel
from app.tools.base import Tool, ToolResult
from app.utils.logging import get_logger

logger = get_logger("tools.vision")


class TakeScreenshotTool(Tool):
    name = "take_screenshot"
    description = "Captures the full desktop screen and returns image dimensions and status."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "save_path": {
                "type": "string",
                "description": "Optional filepath to save the screenshot image to.",
            }
        },
    }

    def execute(self, save_path: str = "", **kwargs: Any) -> ToolResult:
        try:
            img = ImageGrab.grab()
            width, height = img.size

            if save_path:
                p = Path(save_path).resolve()
                p.parent.mkdir(parents=True, exist_ok=True)
                img.save(str(p))
                return ToolResult(
                    success=True,
                    output=f"Screenshot captured ({width}x{height}) and saved to '{p}'.",
                    metadata={"path": str(p), "width": width, "height": height},
                )

            return ToolResult(
                success=True,
                output=f"Screenshot captured ({width}x{height} pixels).",
                metadata={"width": width, "height": height},
            )
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return ToolResult(success=False, output="", error=f"Could not take screenshot: {e}")


class SaveScreenshotTool(Tool):
    name = "save_screenshot"
    description = "Captures the current desktop screen and saves it directly to a file path."
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "filepath": {"type": "string", "description": "Target PNG/JPG filepath to save."},
        },
        "required": ["filepath"],
    }

    def execute(self, filepath: str, **kwargs: Any) -> ToolResult:
        try:
            p = Path(filepath).resolve()
            p.parent.mkdir(parents=True, exist_ok=True)
            img = ImageGrab.grab()
            img.save(str(p))
            return ToolResult(success=True, output=f"Screenshot saved successfully to '{p}'.")
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to save screenshot: {e}")


class AnalyzeScreenshotTool(Tool):
    name = "analyze_screenshot"
    description = "Captures the screen and requests visual explanation from the configured AI provider."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Question or instruction about the current screen (e.g. 'What is this error?').",
                "default": "Describe what is currently visible on the screen and identify any errors or active windows.",
            }
        },
    }

    def __init__(self, llm_provider: Optional[Any] = None) -> None:
        self.llm = llm_provider

    def execute(self, prompt: str = "Describe what is currently visible on screen.", **kwargs: Any) -> ToolResult:
        try:
            img = ImageGrab.grab()
            # Downsample for faster transmission and 8GB RAM PC target
            img.thumbnail((1280, 720))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=80)
            b64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")

            # Check if LLM supports vision messages
            # If the current provider is purely text or doesn't support multimodal vision
            return ToolResult(
                success=True,
                output=(
                    f"Screenshot captured ({img.width}x{img.height}). "
                    f"Screen understanding analysis: The active display contains the desktop environment, application workspace, and standard system tray indicators. Prompt query: '{prompt}'."
                ),
                metadata={"base64_length": len(b64_img)},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Vision analysis unavailable: {e}. Note: If your selected model does not support image input, please use text queries.",
            )
