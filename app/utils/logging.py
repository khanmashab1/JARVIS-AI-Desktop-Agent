"""Structured logging with credential redaction for JARVIS."""

import logging
import re
import sys
from pathlib import Path
from typing import Optional

# Regular expressions and replacements for scrubbing API keys, tokens, and credentials
REDACTION_RULES = [
    (
        re.compile(r'(?i)(api[_-]?key|secret|token|password|bearer|auth|authorization)([\"\']?\s*[:=]\s*[\"\']?)([^\"\'\s,;}{]+)'),
        r'\1\2[REDACTED]',
    ),
    (re.compile(r'sk-[a-zA-Z0-9_\-]{20,}'), '[REDACTED_KEY]'),
    (re.compile(r'tabi-[a-zA-Z0-9_\-]{20,}'), '[REDACTED_KEY]'),
    (re.compile(r'Bearer\s+[a-zA-Z0-9_\.\-]+'), 'Bearer [REDACTED]'),
]


class RedactingFormatter(logging.Formatter):
    """Log formatter that sanitizes secrets before emission."""

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        for pattern, replacement in REDACTION_RULES:
            msg = pattern.sub(replacement, msg)
        return msg


def setup_logger(
    name: str = "jarvis",
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """Configure and return the system root logger with console and file handlers."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    fmt = "%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = RedactingFormatter(fmt, datefmt=datefmt)

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(str(log_file), encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Retrieve a child logger with proper hierarchy."""
    return logging.getLogger(f"jarvis.{name}")
