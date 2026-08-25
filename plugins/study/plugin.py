"""Study Assistant Plugin for JARVIS with Focus Timers and Eye/Attention Monitoring."""

import threading
import time
from typing import Any, Dict, List, Optional

from app.constants import RiskLevel
from app.plugins.base import JarvisPlugin
from app.tools.base import Tool, ToolResult
from app.utils.logging import get_logger

logger = get_logger("plugins.study")


class FocusTimerTool(Tool):
    name = "start_focus_timer"
    description = "Starts a dedicated study focus session or Pomodoro interval (in minutes)."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "duration_minutes": {"type": "integer", "description": "Focus duration in minutes (default 25).", "default": 25},
            "subject": {"type": "string", "description": "Study subject or topic.", "default": "General Study"},
        },
    }

    def __init__(self, plugin: Any) -> None:
        self.plugin = plugin

    def execute(self, duration_minutes: int = 25, subject: str = "General Study", **kwargs: Any) -> ToolResult:
        self.plugin.start_session(duration_minutes=duration_minutes, subject=subject)
        return ToolResult(
            success=True,
            output=f"Focus study session started for {duration_minutes} minutes on '{subject}'. Focus monitoring active.",
        )


class GetStudyStatsTool(Tool):
    name = "get_study_stats"
    description = "Returns historical study focus statistics, completed sessions, and distraction counts."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {"type": "object", "properties": {}}

    def __init__(self, plugin: Any) -> None:
        self.plugin = plugin

    def execute(self, **kwargs: Any) -> ToolResult:
        stats = self.plugin.get_stats()
        return ToolResult(success=True, output=stats)


class StudyPlugin(JarvisPlugin):
    """Study Assistant Plugin with focus timers and eye/attention monitoring."""

    name = "study_assistant"
    version = "1.0.0"
    description = "Assists students with Pomodoro focus sessions, eye closure alerts, and distraction detection."
    author = "JARVIS"

    def __init__(self) -> None:
        super().__init__()
        self.active_session = False
        self.session_start = 0.0
        self.session_duration_minutes = 25
        self.current_subject = "General"
        self.total_focus_minutes = 0
        self.completed_sessions = 0
        self.distraction_warnings = 0

        self.eye_closed_start: Optional[float] = None
        self.eye_closed_threshold = 4.0  # seconds
        self.away_start: Optional[float] = None
        self.away_threshold = 7.0  # seconds

        self.tts_provider = None

    def initialize(self, context: Optional[Dict[str, Any]] = None) -> None:
        if context:
            self.tts_provider = context.get("tts")

    def register_tools(self) -> List[Tool]:
        return [
            FocusTimerTool(self),
            GetStudyStatsTool(self),
        ]

    def start_session(self, duration_minutes: int = 25, subject: str = "General") -> None:
        self.active_session = True
        self.session_start = time.time()
        self.session_duration_minutes = duration_minutes
        self.current_subject = subject
        logger.info(f"Study session started: {subject} ({duration_minutes} min)")

    def process_vision_frame(self, face_result: Any) -> Optional[str]:
        """Evaluate eye closure or looking away signals during active study."""
        if not self.active_session:
            return None

        now = time.time()

        # 1. Prolonged Eye Closure Detection
        if face_result.has_face and face_result.eyes_closed:
            if self.eye_closed_start is None:
                self.eye_closed_start = now
            elif now - self.eye_closed_start >= self.eye_closed_threshold:
                self.distraction_warnings += 1
                self.eye_closed_start = None  # reset
                alert_text = "Uth jao, aankhein kholo aur parhai par focus karo."
                if self.tts_provider:
                    self.tts_provider.speak(alert_text)
                return alert_text
        else:
            self.eye_closed_start = None

        # 2. Looking Away / Absence Detection
        if not face_result.has_face:
            if self.away_start is None:
                self.away_start = now
            elif now - self.away_start >= self.away_threshold:
                self.distraction_warnings += 1
                self.away_start = None  # reset
                alert_text = "Idhar udhar na dekho, parhai par focus karo."
                if self.tts_provider:
                    self.tts_provider.speak(alert_text)
                return alert_text
        else:
            self.away_start = None

        return None

    def get_stats(self) -> Dict[str, Any]:
        return {
            "active_session": self.active_session,
            "current_subject": self.current_subject,
            "completed_sessions": self.completed_sessions,
            "total_focus_minutes": self.total_focus_minutes,
            "distraction_warnings_given": self.distraction_warnings,
        }
