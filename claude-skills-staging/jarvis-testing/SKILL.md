---
name: jarvis-testing
description: Use when writing or running tests for JARVIS. Covers pytest across unit/integration/end-to-end layers for the provider abstraction, tool registry, permission engine, memory, agent, task manager, voice interfaces, plugins, and GUI logic. External services (LLM, network, browser, camera, mic) are always mocked and tests never require a real API key. Triggers include "write tests", "pytest", "mock the LLM", "test coverage", "unit test". Load with jarvis-core; pair with jarvis-debugging.
---

# JARVIS Testing

Tests use **pytest** and must be deterministic, fast, and isolated. No test may require network access or a real API key.

## Layers

```text
Unit         one class/function in isolation
Integration  a few components together (e.g. LLM → tool selection → execution)
End-to-end   a full agent workflow with everything mocked
```

## What to test

Provider abstraction, tool registry, **permission engine** (security-critical), memory, agent loop, task manager, voice interfaces, plugins, and GUI logic (the thin view/service seam — see jarvis-gui).

## Mock all external services

Provide a `MockLLMProvider` implementing `LLMProvider` (jarvis-llm) that returns scripted responses and tool calls. Mock the network, browser (Playwright), camera frames, and microphone audio. This keeps tests free, offline, and repeatable.

## Isolation

Use temporary directories for filesystem tools and a temporary SQLite database for memory (jarvis-memory). Never write to the user's real files or hit real apps during tests.

## Security-focused tests

Explicitly test that HIGH/CRITICAL tools require confirmation, that argument validation rejects bad/malicious input, and that path restrictions hold (jarvis-security).

## Running

Run with `python -m pytest` from the project root. Keep tests under `tests/`, mirroring the app structure.

## Definition of done

Changed behavior is covered by tests, external services are mocked, tests pass locally without credentials, and permission/validation paths for any new MEDIUM+ tool are asserted.
