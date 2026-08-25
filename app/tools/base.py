"""Base tool class and result structures."""

from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional

from app.constants import RiskLevel


@dataclass
class ToolResult:
    """Standardized output returned by every tool execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_llm_string(self) -> str:
        """Format result as string for LLM consumption."""
        if not self.success:
            return f"Error: {self.error or 'Tool execution failed'}"
        if isinstance(self.output, (dict, list)):
            return json.dumps(self.output, indent=2)
        return str(self.output)


class Tool(ABC):
    """Base class for all executable tools in JARVIS."""

    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {"type": "object", "properties": {}, "required": []}
    risk_level: RiskLevel = RiskLevel.SAFE
    requires_confirmation: bool = False

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool action synchronously."""
        raise NotImplementedError

    async def execute_async(self, **kwargs: Any) -> ToolResult:
        """Execute the tool action in a non-blocking thread."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.execute(**kwargs))

    def to_schema(self) -> Dict[str, Any]:
        """Convert tool definition to OpenAI-compatible function schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
