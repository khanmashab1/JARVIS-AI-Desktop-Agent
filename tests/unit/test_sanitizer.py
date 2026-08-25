"""Unit tests for path traversal protection and command sanitization."""

from pathlib import Path
import pytest
from app.security.sanitizer import InputSanitizer, SecurityViolationError


def test_sanitizer_allowed_root(tmp_path: Path):
    allowed_dir = tmp_path / "safe_zone"
    allowed_dir.mkdir()
    sanitizer = InputSanitizer(allowed_roots=[allowed_dir])

    # Valid path inside allowed root
    valid_file = allowed_dir / "test.txt"
    resolved = sanitizer.validate_path(str(valid_file), allow_create=True)
    assert resolved == valid_file.resolve()


def test_sanitizer_blocks_traversal(tmp_path: Path):
    allowed_dir = tmp_path / "safe_zone"
    allowed_dir.mkdir()
    sanitizer = InputSanitizer(allowed_roots=[allowed_dir])

    # Attempt directory traversal outside allowed root
    forbidden = tmp_path / "secret.txt"
    with pytest.raises(SecurityViolationError):
        sanitizer.validate_path(str(forbidden))


def test_sanitizer_command_injection():
    sanitizer = InputSanitizer()

    safe_cmd = ["python", "-m", "pytest"]
    assert sanitizer.sanitize_command(safe_cmd) == safe_cmd

    # Dangerous chained command
    dangerous_cmd = ["python", "-c", "echo test; rm -rf /"]
    with pytest.raises(SecurityViolationError):
        sanitizer.sanitize_command(dangerous_cmd)
