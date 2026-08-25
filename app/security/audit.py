"""Audit logging for security-sensitive tool invocations."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from app.utils.logging import get_logger

logger = get_logger("security.audit")


@dataclass
class AuditRecord:
    timestamp: str
    tool_name: str
    risk_level: str
    arguments: Dict[str, Any]
    approved: bool
    reason: str = ""
    status: str = "EXECUTED"


class AuditLogger:
    """Records security audit events without leaking private secrets."""

    def __init__(self, db_manager: Optional[Any] = None) -> None:
        self.db = db_manager

    def log_action(
        self,
        tool_name: str,
        risk_level: str,
        arguments: Dict[str, Any],
        approved: bool,
        reason: str = "",
        status: str = "EXECUTED",
    ) -> AuditRecord:
        record = AuditRecord(
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            risk_level=risk_level,
            arguments=arguments,
            approved=approved,
            reason=reason,
            status=status,
        )
        logger.info(
            f"AUDIT | Tool: {tool_name} | Risk: {risk_level} | Approved: {approved} | Status: {status}"
        )
        if self.db:
            try:
                self.db.save_audit_record(record)
            except Exception as e:
                logger.error(f"Failed to persist audit log: {e}")
        return record
