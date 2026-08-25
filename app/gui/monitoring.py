"""Real-time System Telemetry and Process Monitoring Page."""

from typing import Any, List
import psutil
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.gui.widgets.metric_card import MetricCard


class MonitoringPage(QWidget):
    """Deep live hardware resource analytics and active process manager."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        title = QLabel("Hardware Telemetry & Process Monitor")
        title.setStyleSheet("color: #F8FAFC; font-size: 20px; font-weight: bold;")
        subtitle = QLabel("Live diagnostics optimized for target PC (Intel i5, 8 GB RAM)")
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Metrics Row
        grid = QGridLayout()
        grid.setSpacing(12)

        self.cpu_card = MetricCard("CPU Usage", "0%", "10-Core Hybrid")
        self.ram_card = MetricCard("RAM Memory", "0 GB", "8.0 GB Physical")
        self.disk_card = MetricCard("Disk Throughput", "C:\\ Ready", "NVMe SSD")
        self.net_card = MetricCard("Network I/O", "0 MB/s", "Packets Transferred")

        grid.addWidget(self.cpu_card, 0, 0)
        grid.addWidget(self.ram_card, 0, 1)
        grid.addWidget(self.disk_card, 0, 2)
        grid.addWidget(self.net_card, 0, 3)
        layout.addLayout(grid)

        # Search Process Filter
        filter_box = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter running processes by name...")
        self.filter_input.setStyleSheet("background-color: #1E293B; color: #F8FAFC; padding: 6px 12px; border-radius: 6px; border: 1px solid #334155;")
        self.filter_input.textChanged.connect(self.refresh_processes)
        filter_box.addWidget(self.filter_input, 1)

        btn_refresh = QPushButton("Refresh Now")
        btn_refresh.setStyleSheet("background-color: #334155; color: #F8FAFC; padding: 6px 14px; border-radius: 6px;")
        btn_refresh.clicked.connect(self.refresh_processes)
        filter_box.addWidget(btn_refresh)
        layout.addLayout(filter_box)

        # Process Table
        self.proc_table = QTableWidget(0, 5)
        self.proc_table.setHorizontalHeaderLabels(["PID", "Process Name", "CPU %", "Memory %", "Action"])
        self.proc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.proc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.proc_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.proc_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.proc_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.proc_table.verticalHeader().setVisible(False)
        self.proc_table.setStyleSheet("""
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
                padding: 6px;
            }
        """)
        layout.addWidget(self.proc_table, 1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_telemetry)
        self.timer.start(2500)
        self.update_telemetry()

    def update_telemetry(self) -> None:
        try:
            # CPU
            cpu = int(psutil.cpu_percent())
            self.cpu_card.update_value(f"{cpu}%", cpu)

            # RAM
            vm = psutil.virtual_memory()
            used_gb = round(vm.used / (1024 ** 3), 1)
            tot_gb = round(vm.total / (1024 ** 3), 1)
            self.ram_card.update_value(f"{used_gb} / {tot_gb} GB", int(vm.percent), f"{vm.percent}% Utilized")

            # Disk
            disk = psutil.disk_usage("C:\\")
            self.disk_card.update_value(f"{round(disk.free / (1024 ** 3), 1)} GB Free", int(disk.percent))

            # Net
            net = psutil.net_io_counters()
            self.net_card.update_value(f"{round(net.bytes_recv / (1024 ** 2), 1)} MB Recv", 50, f"{round(net.bytes_sent / (1024 ** 2), 1)} MB Sent")

            self.refresh_processes()
        except Exception:
            pass

    def refresh_processes(self) -> None:
        q = self.filter_input.text().strip().lower()
        procs = []

        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                name = p.info["name"] or "System"
                if q and q not in name.lower():
                    continue
                procs.append(p.info)
            except Exception:
                continue

        # Sort by memory percent
        procs.sort(key=lambda x: x.get("memory_percent") or 0.0, reverse=True)
        top_procs = procs[:30]

        self.proc_table.setRowCount(len(top_procs))

        for row, info in enumerate(top_procs):
            pid_item = QTableWidgetItem(str(info.get("pid")))
            pid_item.setTextAlignment(Qt.AlignCenter)
            pid_item.setFlags(pid_item.flags() & ~Qt.ItemIsEditable)
            self.proc_table.setItem(row, 0, pid_item)

            name_item = QTableWidgetItem(info.get("name") or "Unknown")
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.proc_table.setItem(row, 1, name_item)

            cpu_item = QTableWidgetItem(f"{info.get('cpu_percent', 0.0):.1f}%")
            cpu_item.setTextAlignment(Qt.AlignCenter)
            cpu_item.setFlags(cpu_item.flags() & ~Qt.ItemIsEditable)
            self.proc_table.setItem(row, 2, cpu_item)

            mem_item = QTableWidgetItem(f"{info.get('memory_percent', 0.0):.1f}%")
            mem_item.setTextAlignment(Qt.AlignCenter)
            mem_item.setFlags(mem_item.flags() & ~Qt.ItemIsEditable)
            self.proc_table.setItem(row, 3, mem_item)

            btn_kill = QPushButton("Kill")
            btn_kill.setStyleSheet("background-color: #7F1D1D; color: #FCA5A5; border: none; border-radius: 4px; padding: 2px 6px;")
            btn_kill.clicked.connect(lambda _, pid=info.get("pid"): self._kill_proc(pid))
            self.proc_table.setCellWidget(row, 4, btn_kill)

    def _kill_proc(self, pid: int) -> None:
        try:
            p = psutil.Process(pid)
            p.terminate()
            self.refresh_processes()
        except Exception:
            pass
