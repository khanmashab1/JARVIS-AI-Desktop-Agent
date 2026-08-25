"""Security policy definitions and risk classification."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set

from app.constants import RiskLevel


@dataclass
class SecurityPolicy:
    """Configurable system security rules."""
    require_confirmation_for_risk: Set[RiskLevel] = field(
        default_factory=lambda: {RiskLevel.HIGH, RiskLevel.CRITICAL}
    )
    allowed_roots: List[Path] = field(default_factory=list)
    blocked_commands: Set[str] = field(
        default_factory=lambda: {
            "rmdir /s /q c:\\", "format", "del /f /s /q c:\\", "mkfs",
            ":(){ :|:& };:", "dd", "shutdown", "reboot"
        }
    )
    allow_shell: bool = False

    def is_confirmation_required(self, risk: RiskLevel) -> bool:
        return risk in self.require_confirmation_for_risk
