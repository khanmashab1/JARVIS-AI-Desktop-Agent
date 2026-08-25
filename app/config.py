"""Configuration management for JARVIS."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from app.constants import (
    DEFAULT_DATABASE_PATH,
    DEFAULT_LOGS_DIR,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MAX_TOKENS,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOOL_TIMEOUT_SECONDS,
    PROJECT_ROOT,
    LLMProviderType,
    STTProviderType,
    TTSProviderType,
)


def _load_env_file(filepath: Path) -> None:
    """Load key-value pairs from a .env file if it exists without overriding existing env."""
    if not filepath.is_file():
        return
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("\'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


@dataclass
class LLMConfig:
    provider: str = LLMProviderType.OPENAI_COMPATIBLE.value
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS
    timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS
    max_iterations: int = DEFAULT_MAX_ITERATIONS


@dataclass
class VoiceConfig:
    enabled: bool = True
    wake_word_enabled: bool = False
    wake_word: str = "hey jarvis"
    stt_provider: str = STTProviderType.FALLBACK.value
    tts_provider: str = TTSProviderType.PYTTSX3.value
    tts_voice: str = ""
    tts_rate: int = 175
    tts_volume: float = 1.0


@dataclass
class VisionConfig:
    enabled: bool = False
    camera_index: int = 0
    study_eye_detection: bool = False
    study_attention_detection: bool = False
    eye_closure_threshold_seconds: float = 4.0
    attention_away_threshold_seconds: float = 7.0


@dataclass
class BrowserConfig:
    enabled: bool = True
    headless: bool = False
    timeout_seconds: float = 30.0


@dataclass
class SecurityConfig:
    require_confirmation_high_risk: bool = True
    require_confirmation_medium_risk: bool = False
    allowed_filesystem_roots: list[str] = field(default_factory=lambda: [str(PROJECT_ROOT.resolve())])
    allow_shell_commands: bool = False


@dataclass
class Config:
    llm: LLMConfig = field(default_factory=LLMConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    database_path: Path = DEFAULT_DATABASE_PATH
    logs_dir: Path = DEFAULT_LOGS_DIR
    log_level: str = "INFO"
    developer_mode: bool = False

    @classmethod
    def load(cls, env_path: Optional[Path] = None) -> Config:
        """Load configuration from environment variables and optional .env file."""
        if env_path is None:
            env_path = PROJECT_ROOT / ".env"
        _load_env_file(env_path)

        llm_cfg = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", LLMProviderType.OPENAI_COMPATIBLE.value),
            base_url=os.getenv("LLM_BASE_URL", ""),
            api_key=os.getenv("LLM_API_KEY", ""),
            model=os.getenv("LLM_MODEL", ""),
            temperature=float(os.getenv("LLM_TEMPERATURE", str(DEFAULT_TEMPERATURE))),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", str(DEFAULT_MAX_TOKENS))),
            timeout_seconds=float(os.getenv("LLM_TIMEOUT", str(DEFAULT_REQUEST_TIMEOUT_SECONDS))),
            max_iterations=int(os.getenv("LLM_MAX_ITERATIONS", str(DEFAULT_MAX_ITERATIONS))),
        )

        voice_cfg = VoiceConfig(
            enabled=os.getenv("ENABLE_VOICE", "true").lower() in ("true", "1", "yes"),
            wake_word_enabled=os.getenv("ENABLE_WAKE_WORD", "false").lower() in ("true", "1", "yes"),
            wake_word=os.getenv("WAKE_WORD", "hey jarvis"),
            stt_provider=os.getenv("STT_PROVIDER", STTProviderType.FALLBACK.value),
            tts_provider=os.getenv("TTS_PROVIDER", TTSProviderType.PYTTSX3.value),
            tts_voice=os.getenv("TTS_VOICE", ""),
            tts_rate=int(os.getenv("TTS_RATE", "175")),
            tts_volume=float(os.getenv("TTS_VOLUME", "1.0")),
        )

        vision_cfg = VisionConfig(
            enabled=os.getenv("ENABLE_CAMERA", "false").lower() in ("true", "1", "yes"),
            camera_index=int(os.getenv("CAMERA_INDEX", "0")),
            study_eye_detection=os.getenv("STUDY_EYE_DETECTION", "false").lower() in ("true", "1", "yes"),
            study_attention_detection=os.getenv("STUDY_ATTENTION_DETECTION", "false").lower() in ("true", "1", "yes"),
            eye_closure_threshold_seconds=float(os.getenv("EYE_CLOSURE_THRESHOLD", "4.0")),
            attention_away_threshold_seconds=float(os.getenv("ATTENTION_AWAY_THRESHOLD", "7.0")),
        )

        browser_cfg = BrowserConfig(
            enabled=os.getenv("ENABLE_BROWSER", "true").lower() in ("true", "1", "yes"),
            headless=os.getenv("BROWSER_HEADLESS", "false").lower() in ("true", "1", "yes"),
            timeout_seconds=float(os.getenv("BROWSER_TIMEOUT", "30.0")),
        )

        sec_roots = os.getenv("ALLOWED_FS_ROOTS", "")
        allowed_roots = [r.strip() for r in sec_roots.split(",") if r.strip()] or [str(PROJECT_ROOT.resolve())]

        security_cfg = SecurityConfig(
            require_confirmation_high_risk=os.getenv("CONFIRM_HIGH_RISK", "true").lower() in ("true", "1", "yes"),
            require_confirmation_medium_risk=os.getenv("CONFIRM_MEDIUM_RISK", "false").lower() in ("true", "1", "yes"),
            allowed_filesystem_roots=allowed_roots,
            allow_shell_commands=os.getenv("ALLOW_SHELL_COMMANDS", "false").lower() in ("true", "1", "yes"),
        )

        db_path_str = os.getenv("DATABASE_PATH", str(DEFAULT_DATABASE_PATH))
        db_path = Path(db_path_str) if Path(db_path_str).is_absolute() else PROJECT_ROOT / db_path_str

        return cls(
            llm=llm_cfg,
            voice=voice_cfg,
            vision=vision_cfg,
            browser=browser_cfg,
            security=security_cfg,
            database_path=db_path,
            logs_dir=DEFAULT_LOGS_DIR,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            developer_mode=os.getenv("DEVELOPER_MODE", "false").lower() in ("true", "1", "yes"),
        )

    def save_to_env(self, env_path: Optional[Path] = None) -> None:
        """Persist current configuration to .env file."""
        if env_path is None:
            env_path = PROJECT_ROOT / ".env"
        lines = [
            f"# JARVIS Configuration",
            f"LLM_PROVIDER={self.llm.provider}",
            f"LLM_BASE_URL={self.llm.base_url}",
            f"LLM_API_KEY={self.llm.api_key}",
            f"LLM_MODEL={self.llm.model}",
            f"LLM_TEMPERATURE={self.llm.temperature}",
            f"LLM_MAX_TOKENS={self.llm.max_tokens}",
            f"",
            f"ENABLE_VOICE={'true' if self.voice.enabled else 'false'}",
            f"ENABLE_WAKE_WORD={'true' if self.voice.wake_word_enabled else 'false'}",
            f"WAKE_WORD={self.voice.wake_word}",
            f"STT_PROVIDER={self.voice.stt_provider}",
            f"TTS_PROVIDER={self.voice.tts_provider}",
            f"TTS_VOICE={self.voice.tts_voice}",
            f"",
            f"ENABLE_CAMERA={'true' if self.vision.enabled else 'false'}",
            f"ENABLE_BROWSER={'true' if self.browser.enabled else 'false'}",
            f"DATABASE_PATH={self.database_path}",
            f"LOG_LEVEL={self.log_level}",
            f"DEVELOPER_MODE={'true' if self.developer_mode else 'false'}",
        ]
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
