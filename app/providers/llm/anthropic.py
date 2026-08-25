"""Anthropic Claude LLM provider implementation."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

from app.providers.llm.base import LLMError, LLMProvider, LLMResponse, ToolCall
from app.utils.logging import get_logger

logger = get_logger("providers.llm.anthropic")


class AnthropicProvider(LLMProvider):
    """Anthropic Messages API client."""

    name = "anthropic"
    supports_native_tools = True

    def __init__(
        self,
        api_key: str = "",
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        timeout_seconds: float = 60.0,
        base_url: str = "https://api.anthropic.com/v1",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.endpoint = f"{base_url.rstrip('/')}/messages"

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        system_prompt = ""
        claude_messages: List[Dict[str, Any]] = []

        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            if role == "system":
                system_prompt += f"{content}\n"
            elif role in ("user", "assistant"):
                claude_messages.append({"role": role, "content": content or ""})
            elif role == "tool":
                claude_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": m.get("tool_call_id", "call_default"),
                            "content": str(content),
                        }
                    ],
                })

        payload: Dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": claude_messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }
        if system_prompt.strip():
            payload["system"] = system_prompt.strip()

        if tools:
            claude_tools = []
            for t in tools:
                fn = t.get("function", {})
                claude_tools.append({
                    "name": fn.get("name"),
                    "description": fn.get("description", ""),
                    "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
                })
            payload["tools"] = claude_tools

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        data = json.dumps(payload).encode("utf-8")
        try:
            loop = asyncio.get_running_loop()
            resp_data = await loop.run_in_executor(
                None,
                self._execute_http,
                self.endpoint,
                data,
                headers,
                self.timeout_seconds,
            )
            return self._parse_response(resp_data)
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise LLMError(f"Anthropic error: {e}", friendly="Anthropic Claude API returned an error.")

    def _execute_http(self, endpoint: str, data: bytes, headers: Dict[str, str], timeout: float) -> Dict[str, Any]:
        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _parse_response(self, data: Dict[str, Any]) -> LLMResponse:
        content_blocks = data.get("content", [])
        text_content = ""
        tool_calls: List[ToolCall] = []

        for block in content_blocks:
            if block.get("type") == "text":
                text_content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.get("id", "call_claude"),
                        name=block.get("name", ""),
                        arguments=block.get("input", {}),
                    )
                )

        return LLMResponse(
            content=text_content or None,
            tool_calls=tool_calls,
            finish_reason=data.get("stop_reason"),
            usage=data.get("usage", {}),
            raw=data,
        )
