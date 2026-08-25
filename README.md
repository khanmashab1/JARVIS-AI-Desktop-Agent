# JARVIS — Complete AI Desktop Agent

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![UI-PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52.svg)](https://doc.qt.io/qtforpython/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**JARVIS** is a developer-grade, modular AI Desktop Agent built in Python. It combines Large Language Model reasoning with controlled desktop automation, speech recognition, local text-to-speech synthesis, browser interaction, persistent SQLite memory, computer vision, and a permission engine with human-in-the-loop security.

The system is optimized for standard hardware (**Intel Core i5, 8 GB RAM, Integrated GPU, Windows 10/11**), using remote LLM reasoning APIs while running lightweight local components for audio, vision, and system telemetry.

---

## 🌟 Core Architecture

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

---

## ✨ Features

- **🧠 Multi-Provider LLM Brain**: Seamlessly interchange between OpenAI-compatible endpoints (TaBiToken, OpenAI, LocalAI), Anthropic Claude Messages, local Ollama models, or deterministic testing mocks.
- **🛡️ Security & Permission Engine**:
  - 5-Tier risk hierarchy: `SAFE`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
  - Dangerous actions (e.g. `delete_file`) trigger an interactive modal approval prompt before execution.
  - Path traversal defense enforcing configured allowed root directories.
  - Secret redaction filter ensuring API keys and credentials are never written to log files.
- **⚡ Controlled Tool Ecosystem**:
  - **Applications**: `open_application`, `close_application`, `list_running_applications`, `focus_application`.
  - **Filesystem**: `create_file`, `read_file`, `write_file`, `append_file`, `create_folder`, `list_directory`, `move_file`, `copy_file`, `rename_file`, `delete_file`, `search_files`.
  - **System**: `get_current_time`, `get_system_information`, `get_cpu_usage`, `get_memory_usage`, `get_disk_usage`, `get_battery_status`, `get_network_status`, `get_volume`, `set_volume`.
  - **Browser**: `open_url`, `search_web`, `browser_back`, `browser_forward`, `refresh_page`, `get_page_title`, `get_page_text`.
  - **Productivity**: `create_note`, `read_note`, `search_notes`, `delete_note`, `create_reminder`, `list_reminders`, `complete_reminder`.
  - **Developer**: `create_project`, `inspect_project`, `read_source_file`, `search_code`, `run_tests`, `get_git_status`.
  - **Vision**: `take_screenshot`, `save_screenshot`, `analyze_screenshot`.
- **💾 SQLite Persistent Memory**:
  - Remembers user facts, preferences, and project names across sessions.
  - Selective context retrieval avoids dumping the entire database into LLM prompts.
- **🎙️ Voice Pipeline**:
  - Voice Activity Detection (VAD) audio listener.
  - Offline SAPI5 Text-to-Speech (`pyttsx3`) and neural TTS (`piper`).
  - Hands-free wake-word detection ("Hey JARVIS") and push-to-talk.
- **👁️ Vision & Study Assistant**:
  - OpenCV webcam monitoring (disabled by default for privacy).
  - Study focus timer / Pomodoro session tracker.
  - Prolonged eye-closure and distraction alerts.
- **🔌 Extensible Plugin Architecture**:
  - Dynamic discovery and loading of custom plugins from `plugins/`.
  - Built-in plugins: `study_assistant`, `developer_assistant`, `system_manager`.
- **🖥️ PySide6 Modern Dark GUI**:
  - Multi-page navigation: Dashboard, Chat, Tasks, Memory, Monitoring, and Settings.
  - Completely non-blocking asynchronous execution via `QThreadPool`.

---

## 🚀 Installation & Setup

### Prerequisites
- Windows 10 or Windows 11
- Python 3.11+ (Python 3.13 tested)

### 1. Clone & Set Up Virtual Environment

```powershell
git clone <repository_url>
cd "JARVIS — AI Desktop Agent"

python -m venv .venv
.venv\Scripts\activate
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file:

```powershell
copy .env.example .env
```

Edit `.env` to configure your LLM provider credentials:

```ini
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_actual_api_key_here
LLM_MODEL=gpt-4o

ENABLE_VOICE=true
ENABLE_CAMERA=false
CONFIRM_HIGH_RISK=true
```

---

## 🖥️ Running JARVIS

Launch the complete desktop application:

```powershell
python run.py
```

Or start via the package entry point:

```powershell
python -m app.main
```

---

## 🧪 Running Tests

Execute the comprehensive automated test suite (30 unit, integration, and acceptance tests):

```powershell
pytest -v
```

---

## 📂 Project Structure

```text
jarvis/
├── app/
│   ├── main.py                     # Application startup & wiring
│   ├── config.py                   # Configuration & .env manager
│   ├── constants.py                # Enums, risk levels & defaults
│   │
│   ├── agent/                      # Core agent reasoning & orchestration
│   │   ├── agent.py                # Reason/Act loop & iteration cap
│   │   ├── planner.py              # Multi-step task planner
│   │   ├── orchestrator.py         # Subsystem event coordinator
│   │   ├── context.py              # Selective memory & prompt context builder
│   │   └── prompts.py              # System prompts & safety guidelines
│   │
│   ├── providers/                  # Provider abstractions & implementations
│   │   ├── llm/                    # OpenAI, Anthropic, Ollama, Mock
│   │   ├── stt/                    # Speech-to-Text (Whisper / Fallback)
│   │   └── tts/                    # Text-to-Speech (pyttsx3 / Piper)
│   │
│   ├── tools/                      # Executable controlled tools
│   │   ├── base.py                 # Tool base class & ToolResult
│   │   ├── registry.py             # Tool registration & schemas
│   │   ├── applications.py         # Desktop app management
│   │   ├── filesystem.py           # Safe file operations
│   │   ├── system.py               # Hardware telemetry & volume
│   │   ├── browser.py              # Web browsing & DuckDuckGo search
│   │   ├── vision.py               # Screenshot capture & analysis
│   │   ├── productivity.py         # Notes & reminders in SQLite
│   │   └── development.py          # Project scaffolding, test runners, Git
│   │
│   ├── memory/                     # Persistent storage
│   │   ├── database.py             # SQLite WAL manager & tables
│   │   ├── manager.py              # Memory facade
│   │   ├── models.py               # Data models
│   │   └── search.py               # Selective keyword search
│   │
│   ├── tasks/                      # Workflow & reminder engine
│   │   ├── manager.py              # Task lifecycle manager
│   │   ├── models.py               # Task & TaskStep models
│   │   └── scheduler.py            # Non-blocking reminder scheduler
│   │
│   ├── security/                   # Protection & permission engine
│   │   ├── permissions.py          # Risk validator & confirmation bridge
│   │   ├── policies.py             # Security rules & blocked commands
│   │   ├── sanitizer.py            # Path traversal & argument validation
│   │   └── audit.py                # Structured security audit logger
│   │
│   ├── voice/                      # Audio listeners & wakeword
│   ├── vision/                     # Camera worker, face/eye detector
│   ├── gui/                        # PySide6 desktop views & widgets
│   ├── plugins/                    # Plugin manager & loader
│   └── utils/                      # Logging (redacted), async & platform utils
│
├── plugins/                        # Dynamic plugins (Study, Developer, System)
├── docs/                           # Architecture, Tools, Security, Plugins docs
├── tests/                          # Automated unit & integration tests
├── .env.example
├── requirements.txt
└── run.py
```

---

## 🔒 Safety & Ethics

JARVIS is an autonomous desktop assistant operating strictly under the user's authority:
1. **No Hidden Actions**: All destructive actions are presented via the confirmation modal.
2. **Privacy First**: The webcam and microphone are disabled unless explicitly enabled. Camera data is processed locally using OpenCV and is never streamed to third parties.
3. **No Credential Theft**: System commands are constrained and sanitized against dangerous injection vectors.

---

## 📄 Documentation

- [Architecture Overview](docs/architecture.md)
- [Tool Reference](docs/tools.md)
- [Plugin System](docs/plugins.md)
- [Security & Permission Model](docs/security.md)
- [Configuration Reference](docs/configuration.md)
