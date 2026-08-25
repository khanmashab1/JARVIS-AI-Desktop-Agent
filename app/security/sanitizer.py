"""Input validation, path traversal defense, and argument sanitization."""

import os
from pathlib import Path
from typing import Any, List, Optional


class SecurityViolationError(Exception):
    """Raised when an operation violates security policies."""
    pass


class InputSanitizer:
    """Validates paths, shell inputs, and tool arguments."""

    def __init__(self, allowed_roots: Optional[List[str | Path]] = None) -> None:
        self.allowed_roots: List[Path] = []
        if allowed_roots:
            for root in allowed_roots:
                self.allowed_roots.append(Path(root).resolve())

    def add_allowed_root(self, root: str | Path) -> None:
        resolved = Path(root).resolve()
        if resolved not in self.allowed_roots:
            self.allowed_roots.append(resolved)

    def validate_path(self, target_path: str | Path, allow_create: bool = False) -> Path:
        """Ensure path is within allowed filesystem roots and free from traversal attacks."""
        if not target_path:
            raise SecurityViolationError("Path cannot be empty.")

        resolved = Path(target_path).resolve()

        # If allowed roots are specified, strictly enforce that resolved path is inside one of them
        if self.allowed_roots:
            is_safe = False
            for root in self.allowed_roots:
                try:
                    resolved.relative_to(root)
                    is_safe = True
                    break
                except ValueError:
                    continue

            if not is_safe:
                raise SecurityViolationError(
                    f"Access denied: Path '{resolved}' is outside allowed directories."
                )
            return resolved

        return resolved

    def sanitize_command(self, cmd_args: List[str]) -> List[str]:
        """Verify command arguments do not contain chained shell injections."""
        if not cmd_args:
            raise SecurityViolationError("Command cannot be empty.")

        dangerous_tokens = {";", "&&", "||", "|", "`", "$"}
        for arg in cmd_args:
            for token in dangerous_tokens:
                if token in arg and not (arg.startswith('"') or arg.startswith("'")):
                    raise SecurityViolationError(f"Dangerous token '{token}' detected in command argument: {arg}")

        return cmd_args
