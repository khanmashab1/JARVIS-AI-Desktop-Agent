"""Unit tests for the permission and security engine."""

from app.constants import RiskLevel
from app.security.permissions import PermissionEngine
from app.security.policies import SecurityPolicy


def test_permission_engine_safe_auto_approved():
    policy = SecurityPolicy()
    engine = PermissionEngine(policy=policy)

    # SAFE tool should auto-approve
    allowed = engine.check_permission(
        tool_name="get_current_time",
        risk_level=RiskLevel.SAFE,
        arguments={},
    )
    assert allowed is True


def test_permission_engine_high_risk_requires_confirmation():
    policy = SecurityPolicy()
    
    # Callback records the prompt and approves
    confirmed = []
    def mock_confirmation(tool_name, desc, risk, args):
        confirmed.append(tool_name)
        return True

    engine = PermissionEngine(policy=policy, confirmation_callback=mock_confirmation)

    allowed = engine.check_permission(
        tool_name="delete_file",
        risk_level=RiskLevel.HIGH,
        arguments={"path": "test.txt"},
    )
    assert allowed is True
    assert "delete_file" in confirmed


def test_permission_engine_user_rejects():
    policy = SecurityPolicy()
    def mock_rejection(tool_name, desc, risk, args):
        return False

    engine = PermissionEngine(policy=policy, confirmation_callback=mock_rejection)

    allowed = engine.check_permission(
        tool_name="delete_file",
        risk_level=RiskLevel.HIGH,
        arguments={"path": "important.db"},
    )
    assert allowed is False
