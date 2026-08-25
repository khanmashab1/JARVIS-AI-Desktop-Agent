"""System-wide constants, enums, risk levels, and defaults for JARVIS."""

from enum import Enum
from pathlib import Path

# Base Paths
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_LOGS_DIR = PROJECT_ROOT / "logs"
DEFAULT_PLUGINS_DIR = PROJECT_ROOT / "plugins"
DEFAULT_DATABASE_PATH = DEFAULT_DATA_DIR / "jarvis.db"


class RiskLevel(str, Enum):
    """Risk classification for tool actions."""
    SAFE = "SAFE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @property
    def requires_confirmation_by_default(self) -> bool:
        return self in (RiskLevel.HIGH, RiskLevel.CRITICAL)


class TaskStatus(str, Enum):
    """Lifecycle states for tracked tasks."""
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class MemoryType(str, Enum):
    """Categories of stored knowledge and context."""
    CONVERSATION = "conversation"
    PREFERENCE = "preference"
    FACT = "fact"
    PROJECT = "project"
    TASK = "task"
    NOTE = "note"


class LLMProviderType(str, Enum):
    """Supported LLM backends."""
    OPENAI_COMPATIBLE = "openai_compatible"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    MOCK = "mock"


class STTProviderType(str, Enum):
    """Supported STT engines."""
    FASTER_WHISPER = "faster_whisper"
    FALLBACK = "fallback"
    MOCK = "mock"


class TTSProviderType(str, Enum):
    """Supported TTS engines."""
    PIPER = "piper"
    PYTTSX3 = "pyttsx3"
    MOCK = "mock"


# Limits & Defaults
DEFAULT_MAX_ITERATIONS = 8
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 4096
DEFAULT_REQUEST_TIMEOUT_SECONDS = 60.0
DEFAULT_TOOL_TIMEOUT_SECONDS = 30.0
DEFAULT_SYSTEM_POLL_INTERVAL_SECONDS = 2.0
