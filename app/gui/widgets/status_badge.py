"""Status Badge indicator with glowing dot."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class StatusBadge(QWidget):
    """Visual status pill (e.g. ONLINE, BUSY, OFFLINE)."""

    def __init__(self, text: str = "ONLINE", status: str = "online", parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self.dot = QLabel("●")
        self.label = QLabel(text)
        self.label.setStyleSheet("font-weight: bold; font-size: 11px; color: #E2E8F0;")

        layout.addWidget(self.dot)
        layout.addWidget(self.label)

        self.set_status(status, text)

    def set_status(self, status: str, text: str = "") -> None:
        if text:
            self.label.setText(text)

        if status.lower() == "online":
            self.dot.setStyleSheet("color: #10B981; font-size: 14px;")
            self.setStyleSheet("background-color: #064E3B; border-radius: 12px; border: 1px solid #059669;")
        elif status.lower() == "busy":
            self.dot.setStyleSheet("color: #F59E0B; font-size: 14px;")
            self.setStyleSheet("background-color: #78350F; border-radius: 12px; border: 1px solid #D97706;")
        else:
            self.dot.setStyleSheet("color: #EF4444; font-size: 14px;")
            self.setStyleSheet("background-color: #7F1D1D; border-radius: 12px; border: 1px solid #DC2626;")
