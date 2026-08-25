---
name: jarvis-gui
description: Use when building or modifying the JARVIS desktop GUI with PySide6 — the dashboard and its pages (Chat, Tasks, Memory, Tools, Vision, System Monitor, Settings, Logs). Enforces a non-blocking, responsive, modern dark interface where all heavy work runs off the UI thread. Triggers include "GUI", "PySide6", "window", "dashboard", "UI", "page", "widget", "frontend", "screen freezes". Load with jarvis-core and jarvis-performance.
---

# JARVIS GUI

The desktop interface is built with **PySide6**. It renders state and dispatches work to the agent/services; it holds no business logic itself. See jarvis-core.

## Pages

```text
Dashboard | Chat | Tasks | Memory | Tools | Vision | System Monitor | Settings | Logs
```

The dashboard shows status (● Online / 🎤 Listening), a conversation area, and quick state.

## Design

Modern, dark, clean, responsive, developer-friendly. Consistent spacing and typography; clear status indicators.

## Non-blocking is the golden rule

**Never** run the LLM, tools, voice, vision, or any I/O on the GUI thread. Offload to `QThread`/`QThreadPool`/worker objects and communicate back via signals/slots (or an async bridge). A frozen window means work is on the UI thread — move it off. See jarvis-performance and jarvis-llm (synchronous `chat()` must run in a worker).

## Thin views

Views call services and render results. Keep agent/tool/memory logic out of widgets so the UI stays testable and swappable (GUI logic can be unit-tested — see jarvis-testing).

## Status & privacy indicators

Surface active tasks (from the task engine), and show when data is sent to a remote LLM and when the camera/microphone is active (jarvis-security, jarvis-vision, jarvis-voice).

## System monitor

Keep monitoring lightweight — periodic, cheap sampling of CPU/RAM/disk/battery/network. No heavy AI inference in the UI loop (jarvis-performance).

## Definition of done

Pages implemented, all heavy work off the UI thread via workers/signals, remote/camera/mic indicators present, monitoring lightweight, and view logic thin enough to test.
