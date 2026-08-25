"""Tasks Management Page for tracking multi-step workflows."""

from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.constants import TaskStatus
from app.tasks.manager import TaskManager
from app.tasks.models import Task


class TasksPage(QWidget):
    """View and manager for long-running and multi-step tasks."""

    task_created = Signal(str, str)

    def __init__(self, task_manager: TaskManager, parent=None) -> None:
        super().__init__(parent)
        self.task_manager = task_manager
        self.task_manager.add_listener(self._on_task_updated)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header_box = QHBoxLayout()
        t_box = QVBoxLayout()
        title = QLabel("Autonomous Task Engine")
        title.setStyleSheet("color: #F8FAFC; font-size: 20px; font-weight: bold;")
        subtitle = QLabel("Track multi-step planning, agent workflows, and execution progress")
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        header_box.addLayout(t_box)
        header_box.addStretch()
        layout.addLayout(header_box)

        # Task Creation Input Box
        create_frame = QFrame()
        create_frame.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        c_layout = QHBoxLayout(create_frame)
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Create a new task (e.g. 'Research Python GUI frameworks and summarize them')...")
        self.task_input.setStyleSheet("""
            QLineEdit {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
            }
        """)
        self.task_input.returnPressed.connect(self._create_task)
        c_layout.addWidget(self.task_input, 1)

        create_btn = QPushButton("Create Task")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        create_btn.clicked.connect(self._create_task)
        c_layout.addWidget(create_btn)
        layout.addWidget(create_frame)

        # Task Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Task Title", "Status", "Progress", "Steps", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
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

        self.refresh_table()

    def _create_task(self) -> None:
        text = self.task_input.text().strip()
        if text:
            self.task_input.clear()
            self.task_manager.create_task(title=text, description=text)
            self.task_created.emit(text, text)
            self.refresh_table()

    def _on_task_updated(self, task: Task) -> None:
        self.refresh_table()

    def refresh_table(self) -> None:
        tasks = self.task_manager.list_tasks()
        self.table.setRowCount(len(tasks))

        for row, task in enumerate(tasks):
            # Title
            title_item = QTableWidgetItem(task.title)
            title_item.setFlags(title_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, title_item)

            # Status
            status_item = QTableWidgetItem(task.status)
            status_item.setTextAlignment(Qt.AlignCenter)
            if task.status == TaskStatus.COMPLETED.value:
                status_item.setForeground(Qt.green)
            elif task.status == TaskStatus.RUNNING.value:
                status_item.setForeground(Qt.cyan)
            elif task.status in (TaskStatus.FAILED.value, TaskStatus.CANCELLED.value):
                status_item.setForeground(Qt.red)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, status_item)

            # Progress
            progress_bar = QProgressBar()
            progress_bar.setValue(task.progress_percent)
            progress_bar.setFixedHeight(14)
            progress_bar.setStyleSheet("QProgressBar { background: #334155; border-radius: 3px; } QProgressBar::chunk { background: #38BDF8; }")
            self.table.setCellWidget(row, 2, progress_bar)

            # Steps count
            steps_item = QTableWidgetItem(f"{len(task.steps)} sub-step(s)")
            steps_item.setTextAlignment(Qt.AlignCenter)
            steps_item.setFlags(steps_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, steps_item)

            # Cancel button
            if task.status in (TaskStatus.PENDING.value, TaskStatus.RUNNING.value):
                btn_cancel = QPushButton("Cancel")
                btn_cancel.setStyleSheet("background-color: #7F1D1D; color: #FCA5A5; border: none; border-radius: 4px; padding: 4px 8px;")
                btn_cancel.clicked.connect(lambda _, t_id=task.id: self.task_manager.cancel_task(t_id))
                self.table.setCellWidget(row, 4, btn_cancel)
            else:
                lbl_done = QLabel("—")
                lbl_done.setAlignment(Qt.AlignCenter)
                lbl_done.setStyleSheet("color: #64748B;")
                self.table.setCellWidget(row, 4, lbl_done)
