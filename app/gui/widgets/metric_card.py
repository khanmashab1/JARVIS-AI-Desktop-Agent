"""Metric card widget displaying telemetry and system stats."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout


class MetricCard(QFrame):
    """Card displaying a single system metric (CPU, RAM, Disk, etc.)."""

    def __init__(self, title: str, value: str = "0%", subtitle: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet("""
            MetricCard {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 8px;
            }
            QLabel {
                border: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600; text-transform: uppercase;")
        layout.addWidget(self.title_label)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #F8FAFC; font-size: 20px; font-weight: bold;")
        layout.addWidget(self.value_label)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #334155;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #38BDF8;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress)

        self.sub_label = QLabel(subtitle)
        self.sub_label.setStyleSheet("color: #64748B; font-size: 11px;")
        layout.addWidget(self.sub_label)

    def update_value(self, value_text: str, percent: int = 0, subtitle: str = "") -> None:
        self.value_label.setText(value_text)
        self.progress.setValue(max(0, min(100, percent)))
        if subtitle:
            self.sub_label.setText(subtitle)
