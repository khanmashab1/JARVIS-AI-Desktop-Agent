"""Tool Call activity card widget."""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class ToolCallCard(QFrame):
    """Visual badge for displaying tool executions in chat or dashboard."""

    def __init__(self, tool_name: str, status: str = "Completed", target: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet("""
            ToolCallCard {
                background-color: #0F172A;
                border: 1px solid #1E293B;
                border-left: 3px solid #38BDF8;
                border-radius: 6px;
                padding: 6px;
            }
            QLabel {
                border: none;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)

        icon_lbl = QLabel("⚙️")
        layout.addWidget(icon_lbl)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.name_lbl = QLabel(f"Tool: <b>{tool_name}</b>")
        self.name_lbl.setStyleSheet("color: #E2E8F0; font-size: 12px;")
        info_layout.addWidget(self.name_lbl)

        if target:
            self.target_lbl = QLabel(f"Target: {target}")
            self.target_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
            info_layout.addWidget(self.target_lbl)

        layout.addLayout(info_layout)
        layout.addStretch()

        self.status_lbl = QLabel(status)
        self.status_lbl.setStyleSheet("color: #34D399; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.status_lbl)
