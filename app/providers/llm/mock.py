"""Deterministic mock LLM provider for unit and integration tests."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from app.providers.llm.base import LLMProvider, LLMResponse, ToolCall


class MockLLMProvider(LLMProvider):
    """Programmable mock provider for testing."""

    name = "mock"
    supports_native_tools = True

    def __init__(self, default_response: str = "Mock response from JARVIS.") -> None:
        self.default_response = default_response
        self.canned_responses: List[LLMResponse] = []
        self.response_generator: Optional[Callable[[List[Dict[str, Any]], Optional[List[Dict[str, Any]]]], LLMResponse]] = None
        self.received_messages: List[List[Dict[str, Any]]] = []
        self.received_tools: List[Optional[List[Dict[str, Any]]]] = []

    def queue_response(self, response: LLMResponse) -> None:
        self.canned_responses.append(response)

    def queue_text(self, text: str) -> None:
        self.canned_responses.append(LLMResponse(content=text))

    def queue_tool_call(self, tool_name: str, arguments: Dict[str, Any], call_id: str = "call_mock_1") -> None:
        self.canned_responses.append(
            LLMResponse(
                content=None,
                tool_calls=[ToolCall(id=call_id, name=tool_name, arguments=arguments)],
            )
        )

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        self.received_messages.append(messages)
        self.received_tools.append(tools)

        if self.response_generator:
            return self.response_generator(messages, tools)

        if self.canned_responses:
            return self.canned_responses.pop(0)

        # Smart fallback for common test queries if no canned responses queued
        last_msg = messages[-1].get("content", "").lower() if messages else ""
        if "time" in last_msg:
            return LLMResponse(
                tool_calls=[ToolCall(id="call_time_1", name="get_current_time", arguments={})]
            )
        if "notepad" in last_msg:
            return LLMResponse(
                tool_calls=[ToolCall(id="call_app_1", name="open_application", arguments={"app_name": "notepad"})]
            )

        return LLMResponse(content=self.default_response)
