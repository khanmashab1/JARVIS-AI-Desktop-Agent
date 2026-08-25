---
name: jarvis-llm
description: Use when adding or changing how JARVIS talks to a language model — the LLM provider abstraction, the initial OpenAI-compatible/TaBiToken backend, adding Anthropic/OpenAI/Gemini/Ollama providers, tool-calling format, retries/backoff, and env-based configuration. Triggers include "LLM provider", "change model", "switch provider", "add Anthropic/Ollama", "tool calling format", "base_url". Load with jarvis-core.
---

# JARVIS LLM

The LLM is the interchangeable "brain." Nothing in the agent or tools may import a concrete provider; they depend only on the abstraction. Swapping providers must never require rewriting the JARVIS core.

## The abstraction (`app/providers/llm/base.py`)

The real interface already in the repo:

```python
class LLMProvider(ABC):
    name: str = "base"
    supports_native_tools: bool = True
    def chat(self, messages, tools=None) -> LLMResponse: ...
```

- `LLMResponse(content, tool_calls, finish_reason, usage, raw)` with `.has_tool_calls`.
- `ToolCall(id, name, arguments)` — a normalized request to run one tool.
- `LLMError(message, friendly=...)` — raise on failure; `friendly` is safe to show/speak.

Every backend translates its vendor payload into this shape, so the agent never sees vendor specifics.

## Initial provider

`OpenAICompatibleProvider` uses the `openai` SDK pointed at a configurable `base_url` (works for TaBiToken and any OpenAI-compatible endpoint).

## Configuration — never hard-code

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
```

Keys and model come from env/`.env` only (see jarvis-security). Do not bake a model name or provider into code.

## Adding a provider (factory pattern)

Add a new module under `app/providers/llm/` implementing `LLMProvider`, then register it in the factory keyed by `LLM_PROVIDER`. **Do not touch the agent** — it already speaks the abstraction. Targets: OpenAI-compatible, Anthropic, OpenAI, Gemini, Ollama/local.

## Tool-calling flow

```text
User → LLM → tool call → validation → permission → execution → tool result → LLM → response
```

The LLM only *selects* tools; execution belongs to the tool + permission layers. **Never** expose PowerShell, CMD, the filesystem, or the network to the LLM outside a registered tool (see jarvis-security).

## Hybrid tool calling

Try native tool calling first. If a provider lacks it, set `supports_native_tools = False`; the agent then uses a JSON-prompt protocol (model emits a structured tool-call object, agent parses and executes). Keep both paths producing the same `ToolCall` objects.

## Reliability

Wrap calls with retries + exponential backoff for transient/network/rate-limit errors; map failures to `LLMError` with a friendly message (e.g. "I couldn't reach the AI provider — check LLM_BASE_URL and your network"). Apply request timeouts.

## Concurrency

`chat()` is synchronous. Callers on the GUI or voice thread must run it in a background worker (QThread/thread pool/executor) so nothing blocks — see jarvis-gui and jarvis-performance. An async provider variant is acceptable as long as it keeps the same normalized interface.

## Privacy

Distinguish LOCAL vs REMOTE. When a request goes to a remote provider, the app should indicate it (jarvis-gui, jarvis-security). Never send secrets/credentials to the model unless explicitly required and approved.
