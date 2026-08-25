---
name: jarvis-performance
description: Use when making performance or resource decisions for JARVIS, which targets modest hardware (Intel i5-1235U, 8 GB RAM, integrated Intel GPU, Windows). Guides avoiding large local models and excessive polling, preferring remote LLMs for heavy reasoning, lightweight local components, asynchronous/background execution, and releasing resources. Triggers include "slow", "laggy", "high CPU", "high RAM", "optimize", "background process", "freezes", "too much memory". Load with jarvis-core; pair with jarvis-gui.
---

# JARVIS Performance

Optimize for the target machine — it is not a workstation:

```text
CPU: Intel Core i5-1235U   RAM: 8 GB   GPU: Integrated Intel   OS: Windows
```

## Rules

- **No large local LLMs.** Use the remote LLM API for heavy reasoning (jarvis-llm). Local models, if any, must be small.
- **Lightweight local components** for STT, TTS, vision, and monitoring (faster-whisper small models, Piper, throttled OpenCV).
- **No unnecessary background processes** and **no excessive polling** — sample system stats on a sensible interval, not in a tight loop.
- **Asynchronous / background execution** for anything slow, so the GUI never blocks (jarvis-gui). The synchronous LLM `chat()` runs in a worker.
- **Cache only where it clearly helps**, and invalidate correctly.
- **Release unused resources** — close browser contexts, camera handles, files, and DB connections.
- **Camera processing is configurable** and off unless enabled (jarvis-vision, jarvis-study).

## Measure first

Don't optimize blindly. Confirm the actual bottleneck (CPU, memory, or blocking I/O) before changing code, and avoid premature optimization that hurts readability (jarvis-core: maintainable beats clever).

## Definition of done

Heavy work is off the UI thread, no large local models loaded, polling/background work is bounded, resources are released, camera stays configurable, and the change is justified by a real measurement.
