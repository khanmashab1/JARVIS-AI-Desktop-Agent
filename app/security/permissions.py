"""Permission engine validating tool calls and handling user confirmations."""

from typing import Any, Callable, Dict, Optional

from app.constants import RiskLevel
from app.security.audit import AuditLogger
from app.security.policies import SecurityPolicy
from app.security.sanitizer import InputSanitizer
from app.utils.logging import get_logger

logger = get_logger("security.permissions")


class PermissionEngine:
    """Enforces risk rules and requests human confirmation when necessary."""

    def __init__(
        self,
        policy: Optional[SecurityPolicy] = None,
        sanitizer: Optional[InputSanitizer] = None,
        audit_logger: Optional[AuditLogger] = None,
        confirmation_callback: Optional[Callable[[str, str, RiskLevel, Dict[str, Any]], bool]] = None,
    ) -> None:
        self.policy = policy or SecurityPolicy()
        self.sanitizer = sanitizer or InputSanitizer()
        self.audit_logger = audit_logger or AuditLogger()
        self.confirmation_callback = confirmation_callback

    def check_permission(
        self,
        tool_name: str,
        risk_level: RiskLevel,
        arguments: Dict[str, Any],
        explicit_requires_confirmation: bool = False,
    ) -> bool:
        """Evaluate if the tool is allowed to execute or requires user approval."""
        needs_confirmation = explicit_requires_confirmation or self.policy.is_confirmation_required(risk_level)

        if not needs_confirmation:
            self.audit_logger.log_action(tool_name, risk_level.value, arguments, approved=True, reason="Auto-approved by policy")
            return True

        if self.confirmation_callback:
            description = f"Execute tool '{tool_name}' with risk level {risk_level.value}"
            approved = self.confirmation_callback(tool_name, description, risk_level, arguments)
            reason = "User approved" if approved else "User rejected"
            self.audit_logger.log_action(tool_name, risk_level.value, arguments, approved=approved, reason=reason, status="APPROVED" if approved else "REJECTED")
            return approved

        logger.warning(f"No confirmation handler for {tool_name} (Risk: {risk_level.value}). Denying execution.")
        self.audit_logger.log_action(tool_name, risk_level.value, arguments, approved=False, reason="No confirmation UI available", status="REJECTED")
        return False
