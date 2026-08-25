"""Navigation Sidebar widget for JARVIS."""

from typing import Callable, Dict
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QWidget):
    """Sidebar menu navigation bar."""

    page_selected = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setStyleSheet("""
            QWidget {
                background-color: #0F172A;
                border-right: 1px solid #1E293B;
            }
            QPushButton {
                background-color: transparent;
                color: #94A3B8;
                text-align: left;
                padding: 12px 16px;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1E293B;
                color: #F8FAFC;
            }
            QPushButton:checked {
                background-color: #1E3A8A;
                color: #60A5FA;
                font-weight: bold;
                border-left: 3px solid #3B82F6;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(6)

        # App Brand Header
        brand_label = QLabel("JARVIS")
        brand_font = QFont("Segoe UI", 16, QFont.Bold)
        brand_label.setFont(brand_font)
        brand_label.setStyleSheet("color: #38BDF8; padding: 4px 8px; border: none;")
        layout.addWidget(brand_label)

        sub_label = QLabel("AI Desktop Agent")
        sub_label.setStyleSheet("color: #64748B; font-size: 11px; padding: 0px 8px 12px 8px; border: none;")
        layout.addWidget(sub_label)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        pages = [
            ("📊  Dashboard", 0),
            ("💬  Chat", 1),
            ("⚡  Tasks", 2),
            ("🧠  Memory", 3),
            ("📈  Monitoring", 4),
            ("⚙️  Settings", 5),
        ]

        self.buttons: Dict[int, QPushButton] = {}

        for text, index in pages:
            btn = QPushButton(text)
            btn.setCheckable(True)
            if index == 0:
                btn.setChecked(True)
            self.button_group.addButton(btn, index)
            layout.addWidget(btn)
            self.buttons[index] = btn

        self.button_group.idClicked.connect(self.page_selected.emit)
        layout.addStretch()

        # Footer Version
        version_label = QLabel("v1.0.0 • Python 3.13")
        version_label.setStyleSheet("color: #475569; font-size: 10px; padding: 8px; border: none;")
        layout.addWidget(version_label)

    def select_page(self, index: int) -> None:
        btn = self.buttons.get(index)
        if btn:
            btn.setChecked(True)
