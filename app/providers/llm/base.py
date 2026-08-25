"""Provider-agnostic LLM abstraction."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolCall:
    """A structured request from the LLM to invoke one tool."""
    id: str
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Normalized response returned by all LLM providers."""
    content: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    finish_reason: Optional[str] = None
    usage: Dict[str, Any] = field(default_factory=dict)
    raw: Any = None

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)


class LLMError(Exception):
    """Raised when an LLM provider encounters an error."""
    def __init__(self, message: str, *, friendly: Optional[str] = None) -> None:
        super().__init__(message)
        self.friendly = friendly or message


class LLMProvider(ABC):
    """Base interface for all LLM backend implementations."""

    name: str = "base"
    supports_native_tools: bool = True

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send messages and tool definitions to the LLM asynchronously."""
        raise NotImplementedError

    def chat_sync(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Synchronous chat wrapper for non-async callers."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, self.chat(messages, tools, **kwargs)).result()
            return loop.run_until_complete(self.chat(messages, tools, **kwargs))
        except RuntimeError:
            return asyncio.run(self.chat(messages, tools, **kwargs))
