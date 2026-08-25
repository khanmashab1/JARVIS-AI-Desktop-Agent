# JARVIS Configuration Guide

JARVIS is configured through environment variables, a local `.env` file, or dynamically via the in-app **Settings** UI.

## Environment Variables Reference

### LLM Provider Settings
- `LLM_PROVIDER`: `openai_compatible` (default), `anthropic`, `ollama`, `mock`.
- `LLM_BASE_URL`: API Base URL (e.g. `https://api.openai.com/v1`, or custom service URL).
- `LLM_API_KEY`: Secret API key for authentication.
- `LLM_MODEL`: Model identifier (e.g. `gpt-4o`, `claude-3-5-sonnet-20241022`, `llama3:latest`).
- `LLM_TEMPERATURE`: Sampling temperature (`0.0` to `1.0`, default `0.2`).
- `LLM_MAX_TOKENS`: Maximum output tokens (default `4096`).
- `LLM_TIMEOUT`: Request timeout in seconds (default `60.0`).
- `LLM_MAX_ITERATIONS`: Maximum consecutive tool execution loops per query (default `8`).

### Voice Settings
- `ENABLE_VOICE`: `true` / `false` to enable speech input and synthetic output.
- `ENABLE_WAKE_WORD`: `true` / `false` to listen continuously for wake phrases.
- `WAKE_WORD`: Phrase to trigger activation (default `hey jarvis`).
- `STT_PROVIDER`: `faster_whisper` or `fallback`.
- `TTS_PROVIDER`: `pyttsx3` (default offline system voice) or `piper`.
- `TTS_RATE`: Speaking speed rate in words per minute (default `175`).

### Vision & Study Assistant Settings
- `ENABLE_CAMERA`: `true` / `false` (default `false` for privacy).
- `CAMERA_INDEX`: Hardware webcam device index (default `0`).
- `STUDY_EYE_DETECTION`: `true` / `false` to detect prolonged eye closure.
- `STUDY_ATTENTION_DETECTION`: `true` / `false` to alert when looking away from the desk.
- `EYE_CLOSURE_THRESHOLD`: Seconds before alerting for closed eyes (default `4.0`).
- `ATTENTION_AWAY_THRESHOLD`: Seconds before alerting for absence (default `7.0`).

### Browser Automation Settings
- `ENABLE_BROWSER`: `true` / `false` (default `true`).
- `BROWSER_HEADLESS`: `true` / `false` (default `false`).
- `BROWSER_TIMEOUT`: Page navigation timeout in seconds (default `30.0`).

### Security Policies
- `CONFIRM_HIGH_RISK`: `true` / `false` (default `true`).
- `CONFIRM_MEDIUM_RISK`: `true` / `false` (default `false`).
- `ALLOWED_FS_ROOTS`: Comma-separated list of allowed absolute paths.
- `ALLOW_SHELL_COMMANDS`: `true` / `false` (default `false`).

### Persistence
- `DATABASE_PATH`: Relative or absolute path to SQLite file (default `data/jarvis.db`).
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`.
