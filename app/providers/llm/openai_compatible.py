"""OpenAI-compatible LLM provider implementation."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

from app.providers.llm.base import LLMError, LLMProvider, LLMResponse, ToolCall
from app.utils.logging import get_logger

logger = get_logger("providers.llm.openai_compatible")


class OpenAICompatibleProvider(LLMProvider):
    """Universal OpenAI-compatible API client (OpenAI, TaBiToken, vLLM, LocalAI, etc.)."""

    name = "openai_compatible"
    supports_native_tools = True

    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        api_key: str = "",
        model: str = "gpt-4o",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        timeout_seconds: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        if not self.base_url.endswith("/chat/completions"):
            self.endpoint = f"{self.base_url}/chat/completions"
        else:
            self.endpoint = self.base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send chat completion request with exponential backoff retries."""
        payload: Dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        if tools and self.supports_native_tools:
            payload["tools"] = tools
            payload["tool_choice"] = kwargs.get("tool_choice", "auto")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "JARVIS-Desktop-Agent/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        data = json.dumps(payload).encode("utf-8")
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                # Run HTTP request in background worker to prevent event loop blocking
                loop = asyncio.get_running_loop()
                response_data = await loop.run_in_executor(
                    None,
                    self._execute_http_request,
                    self.endpoint,
                    data,
                    headers,
                    self.timeout_seconds,
                )
                return self._parse_response(response_data)
            except urllib.error.HTTPError as he:
                status = he.code
                err_body = he.read().decode("utf-8", errors="replace")
                logger.warning(f"LLM HTTP error {status} on attempt {attempt}/{self.max_retries}: {err_body[:200]}")
                if status == 401:
                    raise LLMError(
                        f"Authentication failed (HTTP 401). Please verify your API Key.",
                        friendly="Authentication failed. Please verify your LLM API Key in Settings.",
                    )
                if status in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise LLMError(
                    f"LLM API returned HTTP {status}: {err_body}",
                    friendly=f"The AI provider returned an error (HTTP {status}).",
                )
            except urllib.error.URLError as ue:
                logger.warning(f"LLM connection error on attempt {attempt}/{self.max_retries}: {ue.reason}")
                last_exception = ue
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
            except TimeoutError as te:
                logger.warning(f"LLM timeout on attempt {attempt}/{self.max_retries}")
                last_exception = te
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
            except Exception as ex:
                logger.error(f"Unexpected error in LLM call: {ex}")
                raise LLMError(str(ex), friendly="An unexpected error occurred while communicating with the AI service.")

        raise LLMError(
            f"Failed to connect to LLM provider after {self.max_retries} attempts: {last_exception}",
            friendly="Unable to connect to the AI service. Please check your network and provider URL.",
        )

    def _execute_http_request(
        self, endpoint: str, data: bytes, headers: Dict[str, str], timeout: float
    ) -> Dict[str, Any]:
        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp_body = resp.read().decode("utf-8")
            return json.loads(resp_body)

    def _parse_response(self, data: Dict[str, Any]) -> LLMResponse:
        try:
            choice = data["choices"][0]
            message = choice["message"]
            content = message.get("content")
            tool_calls_raw = message.get("tool_calls", [])

            parsed_tool_calls: List[ToolCall] = []
            for tc in tool_calls_raw:
                tc_id = tc.get("id", "call_default")
                fn = tc.get("function", {})
                name = fn.get("name", "")
                arg_str = fn.get("arguments", "{}")
                try:
                    args = json.loads(arg_str) if isinstance(arg_str, str) else arg_str
                except Exception:
                    args = {}
                parsed_tool_calls.append(ToolCall(id=tc_id, name=name, arguments=args))

            return LLMResponse(
                content=content,
                tool_calls=parsed_tool_calls,
                finish_reason=choice.get("finish_reason"),
                usage=data.get("usage", {}),
                raw=data,
            )
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}. Raw data: {data}")
            raise LLMError(f"Malformed LLM response format: {e}", friendly="Received an unrecognized response format from the AI provider.")
