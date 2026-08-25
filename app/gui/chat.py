"""Interactive Chat Page for JARVIS Desktop Agent."""

from typing import Any, Callable, Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.gui.widgets.tool_call_card import ToolCallCard


class ChatBubble(QFrame):
    """Message bubble for User or JARVIS."""

    def __init__(self, sender: str, text: str, is_user: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"""
            ChatBubble {{
                background-color: {'#2563EB' if is_user else '#1E293B'};
                border: 1px solid {'#3B82F6' if is_user else '#334155'};
                border-radius: 12px;
                padding: 10px 14px;
            }}
            QLabel {{ border: none; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        header = QLabel("You" if is_user else "JARVIS")
        header.setStyleSheet(f"font-weight: bold; font-size: 11px; color: {'#93C5FD' if is_user else '#38BDF8'};")
        layout.addWidget(header)

        content = QLabel(text)
        content.setWordWrap(True)
        content.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content.setStyleSheet("color: #F8FAFC; font-size: 13px; line-height: 1.4;")
        layout.addWidget(content)


class ChatPage(QWidget):
    """Chat interface allowing text commands and voice interactions."""

    message_submitted = Signal(str)
    voice_toggled = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        header = QLabel("JARVIS Intelligence Hub")
        header.setStyleSheet("color: #F8FAFC; font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        # Scroll Area for Messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #0B0F17;
                border: 1px solid #1E293B;
                border-radius: 10px;
            }
        """)

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background-color: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(16, 16, 16, 16)
        self.chat_layout.setSpacing(14)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_container)
        layout.addWidget(self.scroll_area, 1)

        # Status Line
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #38BDF8; font-size: 11px; font-style: italic;")
        layout.addWidget(self.status_lbl)

        # Input Row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setFixedSize(42, 42)
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 21px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """)
        self.mic_btn.clicked.connect(self.voice_toggled.emit)
        input_row.addWidget(self.mic_btn)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message or command for JARVIS (e.g. 'Open Notepad', 'What is my RAM?')...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #38BDF8;
            }
        """)
        self.input_field.returnPressed.connect(self._on_send)
        input_row.addWidget(self.input_field, 1)

        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedHeight(42)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        self.send_btn.clicked.connect(self._on_send)
        input_row.addWidget(self.send_btn)

        layout.addLayout(input_row)

        # Welcome message
        self.add_message("JARVIS", "Greetings! I am JARVIS. How may I assist you with desktop automation, file management, or development today?", is_user=False)

    def _on_send(self) -> None:
        text = self.input_field.text().strip()
        if text:
            self.input_field.clear()
            self.add_message("You", text, is_user=True)
            self.set_status("JARVIS is thinking...")
            self.message_submitted.emit(text)

    def add_message(self, sender: str, text: str, is_user: bool = False) -> None:
        bubble = ChatBubble(sender=sender, text=text, is_user=is_user)
        # Insert before stretch
        count = self.chat_layout.count()
        self.chat_layout.insertWidget(count - 1, bubble)
        self._scroll_to_bottom()

    def add_tool_activity(self, tool_name: str, status: str = "Completed", target: str = "") -> None:
        card = ToolCallCard(tool_name=tool_name, status=status, target=target)
        count = self.chat_layout.count()
        self.chat_layout.insertWidget(count - 1, card)
        self._scroll_to_bottom()

    def set_status(self, status_text: str) -> None:
        self.status_lbl.setText(status_text)

    def set_mic_active(self, active: bool) -> None:
        if active:
            self.mic_btn.setStyleSheet("""
                QPushButton {
                    background-color: #DC2626;
                    color: #FFFFFF;
                    border: 2px solid #EF4444;
                    border-radius: 21px;
                    font-size: 16px;
                }
            """)
            self.set_status("🎤 Listening for voice command...")
        else:
            self.mic_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1E293B;
                    color: #F8FAFC;
                    border: 1px solid #334155;
                    border-radius: 21px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #334155;
                }
            """)
            self.set_status("")

    def _scroll_to_bottom(self) -> None:
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
