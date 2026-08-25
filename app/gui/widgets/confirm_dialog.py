"""Confirmation dialog modal for high-risk tool execution approvals."""

from typing import Any, Dict
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)
from app.constants import RiskLevel


class ConfirmDialog(QDialog):
    """Modal dialog prompting human confirmation before dangerous operations."""

    def __init__(
        self,
        tool_name: str,
        description: str,
        risk_level: RiskLevel,
        arguments: Dict[str, Any],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("JARVIS Permission Request")
        self.setFixedWidth(460)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #0F172A;
                border: 1px solid #334155;
                border-radius: 12px;
            }
            QLabel {
                color: #F8FAFC;
            }
            QTextEdit {
                background-color: #1E293B;
                color: #CBD5E1;
                border: 1px solid #334155;
                border-radius: 6px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
            QPushButton#rejectBtn {
                background-color: #334155;
                color: #F8FAFC;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton#rejectBtn:hover {
                background-color: #475569;
            }
            QPushButton#approveBtn {
                background-color: #DC2626;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton#approveBtn:hover {
                background-color: #EF4444;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("⚠️ JARVIS Security Confirmation")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #F87171;")
        layout.addWidget(title)

        info_lbl = QLabel(f"<b>Action:</b> {tool_name}<br><b>Risk Level:</b> <span style='color: #EF4444;'>{risk_level.value}</span>")
        info_lbl.setStyleSheet("font-size: 13px; color: #E2E8F0;")
        layout.addWidget(info_lbl)

        desc_lbl = QLabel(description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(desc_lbl)

        # Arguments preview
        arg_text = QTextEdit()
        arg_text.setReadOnly(True)
        import json
        arg_text.setPlainText(json.dumps(arguments, indent=2))
        arg_text.setFixedHeight(90)
        layout.addWidget(arg_text)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.reject_btn = QPushButton("Reject / Cancel")
        self.reject_btn.setObjectName("rejectBtn")
        self.reject_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.reject_btn)

        self.approve_btn = QPushButton("Approve Action")
        self.approve_btn.setObjectName("approveBtn")
        self.approve_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.approve_btn)

        layout.addLayout(btn_layout)
