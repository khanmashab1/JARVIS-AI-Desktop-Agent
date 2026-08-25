"""Ollama local LLM provider implementation."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

from app.providers.llm.base import LLMError, LLMProvider, LLMResponse, ToolCall
from app.utils.logging import get_logger

logger = get_logger("providers.llm.ollama")


class OllamaProvider(LLMProvider):
    """Local Ollama client."""

    name = "ollama"
    supports_native_tools = True

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3:latest",
        temperature: float = 0.2,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")
        self.endpoint = f"{self.base_url}/api/chat"
        self.model = model
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        payload: Dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
            },
        }
        if tools:
            payload["tools"] = tools

        headers = {"Content-Type": "application/json"}
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
        except urllib.error.URLError as ue:
            logger.warning(f"Ollama connection error: {ue}")
            raise LLMError(
                f"Cannot connect to local Ollama instance at {self.base_url}: {ue}",
                friendly="Local Ollama service is not running. Please start Ollama or select another provider in Settings.",
            )
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise LLMError(f"Ollama error: {e}", friendly="Ollama local LLM encountered an error.")

    def _execute_http(self, endpoint: str, data: bytes, headers: Dict[str, str], timeout: float) -> Dict[str, Any]:
        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _parse_response(self, data: Dict[str, Any]) -> LLMResponse:
        msg = data.get("message", {})
        content = msg.get("content")
        raw_tools = msg.get("tool_calls", [])
        tool_calls: List[ToolCall] = []

        for i, tc in enumerate(raw_tools):
            fn = tc.get("function", {})
            tool_calls.append(
                ToolCall(
                    id=f"ollama_call_{i}",
                    name=fn.get("name", ""),
                    arguments=fn.get("arguments", {}),
                )
            )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=data.get("done_reason"),
            usage={"total_duration": data.get("total_duration")},
            raw=data,
        )
