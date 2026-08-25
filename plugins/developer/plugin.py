"""Developer Assistant Plugin for JARVIS."""

from typing import Any, Dict, List, Optional

from app.plugins.base import JarvisPlugin
from app.tools.base import Tool
from app.tools.development import (
    CreateProjectTool,
    GetGitStatusTool,
    InspectProjectTool,
    ReadSourceFileTool,
    RunTestsTool,
    SearchCodeTool,
)


class DeveloperPlugin(JarvisPlugin):
    """Developer Assistant providing code inspection, git telemetry, and testing."""

    name = "developer_assistant"
    version = "1.0.0"
    description = "Provides project scaffolding, code search, Git inspection, and test execution."
    author = "JARVIS"

    def register_tools(self) -> List[Tool]:
        return [
            CreateProjectTool(),
            InspectProjectTool(),
            ReadSourceFileTool(),
            SearchCodeTool(),
            RunTestsTool(),
            GetGitStatusTool(),
        ]
