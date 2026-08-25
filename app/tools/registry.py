"""Tool registry managing tool lifecycle, discovery, and schemas."""

from typing import Any, Dict, List, Optional
from app.tools.base import Tool
from app.utils.logging import get_logger

logger = get_logger("tools.registry")


class ToolRegistry:
    """Central repository of registered tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}
        self._enabled: Dict[str, bool] = {}

    def register(self, tool: Tool, enabled: bool = True) -> None:
        """Register a tool instance."""
        if not tool.name:
            raise ValueError(f"Tool {tool.__class__.__name__} must specify a unique 'name'.")
        self._tools[tool.name] = tool
        self._enabled[tool.name] = enabled
        logger.debug(f"Registered tool: {tool.name} (Risk: {tool.risk_level.value})")

    def unregister(self, tool_name: str) -> bool:
        if tool_name in self._tools:
            del self._tools[tool_name]
            del self._enabled[tool_name]
            return True
        return False

    def get(self, tool_name: str) -> Optional[Tool]:
        return self._tools.get(tool_name)

    def is_enabled(self, tool_name: str) -> bool:
        return self._enabled.get(tool_name, False)

    def set_enabled(self, tool_name: str, enabled: bool) -> None:
        if tool_name in self._tools:
            self._enabled[tool_name] = enabled

    def get_all_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def get_enabled_tools(self) -> List[Tool]:
        return [tool for name, tool in self._tools.items() if self._enabled.get(name, False)]

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Return list of function schemas for enabled tools to pass to LLM."""
        return [tool.to_schema() for tool in self.get_enabled_tools()]
