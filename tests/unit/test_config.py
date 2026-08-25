"""Unit tests for configuration loading and persistence."""

import os
from pathlib import Path
from app.config import Config


def test_config_defaults(tmp_path: Path):
    env_file = tmp_path / ".env"
    cfg = Config.load(env_path=env_file)

    assert cfg.llm.provider == "openai_compatible"
    assert cfg.llm.temperature == 0.2
    assert cfg.llm.max_iterations == 8
    assert cfg.voice.enabled is True
    assert cfg.security.require_confirmation_high_risk is True


def test_config_save_and_reload(tmp_path: Path):
    env_file = tmp_path / ".env"
    cfg = Config.load(env_path=env_file)
    cfg.llm.provider = "anthropic"
    cfg.llm.model = "claude-3-5-sonnet"
    cfg.llm.api_key = "test_key_123"
    cfg.save_to_env(env_path=env_file)

    assert env_file.exists()
    content = env_file.read_text(encoding="utf-8")
    assert "LLM_PROVIDER=anthropic" in content
    assert "LLM_MODEL=claude-3-5-sonnet" in content

    # Reload
    reloaded = Config.load(env_path=env_file)
    assert reloaded.llm.provider == "anthropic"
    assert reloaded.llm.model == "claude-3-5-sonnet"
