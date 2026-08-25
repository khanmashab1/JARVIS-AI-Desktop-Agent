"""Memory Explorer Page for inspecting and managing persistent memories."""

from typing import Any, List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.constants import MemoryType
from app.memory.manager import MemoryManager
from app.memory.models import MemoryItem


class MemoryPage(QWidget):
    """Visual explorer and manager for JARVIS SQLite memory database."""

    def __init__(self, memory_manager: MemoryManager, parent=None) -> None:
        super().__init__(parent)
        self.memory = memory_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        title = QLabel("Persistent Memory Store")
        title.setStyleSheet("color: #F8FAFC; font-size: 20px; font-weight: bold;")
        subtitle = QLabel("Selective long-term knowledge, preferences, project facts, and user context")
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Filter & Search Row
        search_frame = QFrame()
        search_frame.setStyleSheet("background-color: #1E293B; border-radius: 8px; padding: 6px;")
        s_layout = QHBoxLayout(search_frame)

        self.type_filter = QComboBox()
        self.type_filter.addItems(["ALL TYPES", "fact", "preference", "project", "task", "note"])
        self.type_filter.setStyleSheet("background-color: #0F172A; color: #F8FAFC; padding: 6px 12px; border-radius: 6px;")
        self.type_filter.currentTextChanged.connect(self.refresh_memories)
        s_layout.addWidget(self.type_filter)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search stored memories by keyword or key...")
        self.search_input.setStyleSheet("background-color: #0F172A; color: #F8FAFC; padding: 6px 12px; border-radius: 6px; border: 1px solid #334155;")
        self.search_input.textChanged.connect(self.refresh_memories)
        s_layout.addWidget(self.search_input, 1)

        layout.addWidget(search_frame)

        # Add Memory Row
        add_frame = QFrame()
        add_frame.setStyleSheet("background-color: #1E293B; border-radius: 8px; padding: 6px;")
        a_layout = QHBoxLayout(add_frame)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Key (e.g. 'main_project', 'favorite_ide')...")
        self.key_input.setStyleSheet("background-color: #0F172A; color: #F8FAFC; padding: 6px; border-radius: 4px;")
        a_layout.addWidget(self.key_input, 1)

        self.val_input = QLineEdit()
        self.val_input.setPlaceholderText("Content / Fact (e.g. 'NEXUS Autonomous System')...")
        self.val_input.setStyleSheet("background-color: #0F172A; color: #F8FAFC; padding: 6px; border-radius: 4px;")
        a_layout.addWidget(self.val_input, 2)

        self.add_type_combo = QComboBox()
        self.add_type_combo.addItems(["fact", "preference", "project", "task", "note"])
        self.add_type_combo.setStyleSheet("background-color: #0F172A; color: #F8FAFC; padding: 6px;")
        a_layout.addWidget(self.add_type_combo)

        btn_add = QPushButton("Remember Fact")
        btn_add.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; border-radius: 4px; padding: 6px 14px;")
        btn_add.clicked.connect(self._add_memory)
        a_layout.addWidget(btn_add)

        layout.addWidget(add_frame)

        # Memory Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Type", "Key", "Content", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0B0F17;
                border: 1px solid #1E293B;
                border-radius: 8px;
                color: #E2E8F0;
                gridline-color: #1E293B;
            }
            QHeaderView::section {
                background-color: #1E293B;
                color: #94A3B8;
                font-weight: bold;
                border: none;
                padding: 8px;
            }
        """)
        layout.addWidget(self.table, 1)

        self.refresh_memories()

    def _add_memory(self) -> None:
        key = self.key_input.text().strip()
        val = self.val_input.text().strip()
        mtype = self.add_type_combo.currentText()
        if key and val:
            self.memory.save_memory(key=key, content=val, memory_type=mtype)
            self.key_input.clear()
            self.val_input.clear()
            self.refresh_memories()

    def _delete_memory(self, memory_id: str) -> None:
        self.memory.delete_memory(memory_id)
        self.refresh_memories()

    def refresh_memories(self) -> None:
        filter_type = self.type_filter.currentText()
        search_q = self.search_input.text().strip().lower()

        if filter_type != "ALL TYPES":
            memories = self.memory.list_memories(filter_type)
        else:
            memories = self.memory.list_memories()

        if search_q:
            memories = [
                m for m in memories
                if search_q in m.key.lower() or search_q in m.content.lower() or search_q in m.memory_type.lower()
            ]

        self.table.setRowCount(len(memories))

        for row, mem in enumerate(memories):
            type_item = QTableWidgetItem(mem.memory_type.upper())
            type_item.setTextAlignment(Qt.AlignCenter)
            type_item.setForeground(Qt.cyan)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, type_item)

            key_item = QTableWidgetItem(mem.key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, key_item)

            val_item = QTableWidgetItem(mem.content)
            val_item.setFlags(val_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, val_item)

            btn_del = QPushButton("Forget")
            btn_del.setStyleSheet("background-color: #7F1D1D; color: #FCA5A5; border: none; border-radius: 4px; padding: 4px 8px;")
            btn_del.clicked.connect(lambda _, m_id=mem.id: self._delete_memory(m_id))
            self.table.setCellWidget(row, 3, btn_del)
