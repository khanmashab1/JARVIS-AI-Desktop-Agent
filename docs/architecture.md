# JARVIS Architecture

JARVIS is a modular AI Desktop Agent where **the Large Language Model is the reasoning brain** and **Python is the controlled execution layer**. The LLM never touches the operating system directly; every interaction passes through a structured tool definition, validation, and a security permission engine.

## High-Level Architecture

```text
                         USER
                           │
                ┌──────────┴──────────┐
                │                     │
             VOICE                  TEXT
                │                     │
                ↓                     ↓
          Speech-to-Text          GUI Chat (PySide6)
                │                     │
                └──────────┬──────────┘
                           ↓
                    JARVIS AGENT
                           │
             ┌─────────────┼─────────────┐
             │             │             │
          Planner        Memory        Context
             │             │             │
             └─────────────┼─────────────┘
                           ↓
                     LLM PROVIDER (OpenAI / Anthropic / Ollama / Custom)
                           │
                     Tool Selection
                           │
                  PERMISSION ENGINE (SAFE / LOW / MED / HIGH / CRITICAL)
                           │
                     TOOL EXECUTOR
                           │
      ┌────────────┬───────┼────────┬────────────┐
      ↓            ↓       ↓        ↓            ↓
   Desktop      Browser   Files   System      Vision
      │            │       │        │            │
      └────────────┴───────┼────────┴────────────┘
                           ↓
                     Tool Results
                           ↓
                      LLM / Agent
                           ↓
                   Final Response
                           │
                   Text-to-Speech
                           │
                         USER
```

## Subsystem Responsibilities

1. **Agent Engine (`app/agent/`)**:
   - `JarvisAgent`: Manages the Reason/Act iterative loop, tool invocation, iteration cap (default 8), and error recovery.
   - `ContextBuilder`: Assembles prompt context, system instructions, and selectively queries SQLite memory to inject only relevant facts without overflowing context windows.
   - `JarvisOrchestrator`: Coordinates the event bus between GUI/voice, agent execution, task tracking, and persistence.

2. **Provider Layer (`app/providers/`)**:
   - `LLMProvider`: Abstract interface for chat completions and tool calling.
   - `OpenAICompatibleProvider`: Universal client for OpenAI, TaBiToken, vLLM, and any standard endpoint.
   - `AnthropicProvider`: Claude Messages API client with native tool use.
   - `OllamaProvider`: Local offline LLM backend.
   - `STTProvider` & `TTSProvider`: Speech transcription (`faster-whisper` / fallback) and speech synthesis (`pyttsx3` / `piper`).

3. **Tool System (`app/tools/`)**:
   - Unified `Tool` base class with schema export, risk level tags, and sync/async runners.
   - `ToolRegistry`: Manages enabled tools and translates them into LLM function specifications.

4. **Security & Permissions (`app/security/`)**:
   - `PermissionEngine`: Decides if an action executes directly or requires human approval.
   - `InputSanitizer`: Strictly enforces allowed filesystem roots and prevents path traversal / shell injection.
   - `AuditLogger`: Persists structured audit records without leaking credentials.

5. **Memory Subsystem (`app/memory/`)**:
   - SQLite with WAL mode (`data/jarvis.db`).
   - Tables: `conversations`, `messages`, `memories`, `tasks`, `notes`, `reminders`, `tool_logs`, `settings`.
   - `MemorySearcher`: Keyword and semantic ranking for selective context retrieval.

6. **Task Engine (`app/tasks/`)**:
   - Manages multi-step workflows across lifecycle states: `PENDING`, `PLANNING`, `RUNNING`, `WAITING_FOR_CONFIRMATION`, `COMPLETED`, `FAILED`, `CANCELLED`.
   - `ReminderScheduler`: Non-blocking background timer loop for reminders and scheduled actions.

7. **Plugin System (`app/plugins/`)**:
   - Extensible plugin architecture with dynamic discovery and error isolation.
   - Example plugins: `study_assistant`, `developer_assistant`, `system_manager`.

8. **Desktop GUI (`app/gui/`)**:
   - PySide6 application with dark mode styling.
   - Asynchronous execution via `QThreadPool` to ensure the UI never blocks.
