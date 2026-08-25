"""Sci-Fi Iron Man HUD Dashboard with Animated Arc Reactor, Live Weather, and Voice HUD."""

from datetime import datetime
from typing import Any, Callable, Dict, Optional
import psutil
from PySide6.QtCore import QDateTime, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.config import Config
from app.gui.widgets.arc_reactor import ArcReactorWidget
from app.gui.widgets.metric_card import MetricCard
from app.gui.widgets.status_badge import StatusBadge
from app.tools.weather import GetWeatherTool


class DashboardPage(QWidget):
    """Futuristic holographic Iron Man / JARVIS HUD Overview Dashboard."""

    action_requested = Signal(str)
    voice_toggled = Signal()

    def __init__(self, config: Config, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.weather_tool = GetWeatherTool()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)

        # 1. Top HUD Header Bar
        top_hud = QFrame()
        top_hud.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #091322, stop:0.5 #0F1E36, stop:1 #091322);
                border: 1px solid #00f0ff;
                border-radius: 10px;
                padding: 6px 14px;
            }
            QLabel { border: none; }
        """)
        top_layout = QHBoxLayout(top_hud)
        top_layout.setContentsMargins(8, 4, 8, 4)

        # System Protocol Title
        proto_box = QVBoxLayout()
        proto_title = QLabel("JARVIS HUD // PROTOCOL MARK-85")
        proto_title.setStyleSheet("color: #00f0ff; font-family: Consolas, monospace; font-size: 13px; font-weight: bold; letter-spacing: 2px;")
        proto_sub = QLabel(f"AI CORE: {self.config.llm.model.upper()} (TaBiToken) • SECURE HOST")
        proto_sub.setStyleSheet("color: #64748B; font-size: 10px; font-weight: 600;")
        proto_box.addWidget(proto_title)
        proto_box.addWidget(proto_sub)
        top_layout.addLayout(proto_box)

        top_layout.addStretch()

        # Digital HUD Clock
        self.clock_lbl = QLabel("00:00:00")
        self.clock_lbl.setStyleSheet("color: #38BDF8; font-family: Consolas, monospace; font-size: 20px; font-weight: bold; padding: 0 16px;")
        top_layout.addWidget(self.clock_lbl)

        top_layout.addStretch()

        # Live Weather Widget Card
        weather_frame = QFrame()
        weather_frame.setStyleSheet("background-color: #0B192E; border: 1px solid #1E3A8A; border-radius: 6px; padding: 4px 10px;")
        w_layout = QHBoxLayout(weather_frame)
        w_layout.setContentsMargins(6, 2, 6, 2)
        w_layout.setSpacing(8)

        w_icon = QLabel("🌤️")
        w_icon.setStyleSheet("font-size: 16px;")
        w_layout.addWidget(w_icon)

        w_info = QVBoxLayout()
        w_info.setSpacing(0)
        self.weather_temp_lbl = QLabel("Fetching weather...")
        self.weather_temp_lbl.setStyleSheet("color: #F8FAFC; font-weight: bold; font-size: 12px;")
        self.weather_desc_lbl = QLabel("Local Weather")
        self.weather_desc_lbl.setStyleSheet("color: #94A3B8; font-size: 10px;")
        w_info.addWidget(self.weather_temp_lbl)
        w_info.addWidget(self.weather_desc_lbl)
        w_layout.addLayout(w_info)

        btn_w_refresh = QPushButton("↻")
        btn_w_refresh.setFixedSize(22, 22)
        btn_w_refresh.setStyleSheet("background: transparent; color: #38BDF8; border: none; font-weight: bold; font-size: 14px;")
        btn_w_refresh.clicked.connect(self.update_weather)
        w_layout.addWidget(btn_w_refresh)

        top_layout.addWidget(weather_frame)
        main_layout.addWidget(top_hud)

        # 2. Main HUD Body: Left Gauges | Center Arc Reactor | Right Controls
        body_layout = QHBoxLayout()
        body_layout.setSpacing(14)

        # Left HUD Panel: Hardware Telemetry
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #0B1322;
                border: 1px solid #1E293B;
                border-left: 3px solid #00f0ff;
                border-radius: 10px;
                padding: 10px;
            }
            QLabel { border: none; }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)

        l_title = QLabel("CORE TELEMETRY ARRAY")
        l_title.setStyleSheet("color: #00f0ff; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        left_layout.addWidget(l_title)

        self.cpu_card = MetricCard("CPU REACTOR", "0%", "10-Core Multi-Thread")
        self.ram_card = MetricCard("MEMORY RAM", "0 GB", "8.0 GB Physical")
        self.disk_card = MetricCard("SYSTEM STORAGE", "0 GB", "C: Drive SSD")
        self.power_card = MetricCard("POWER MATRIX", "100%", "AC Connected")

        left_layout.addWidget(self.cpu_card)
        left_layout.addWidget(self.ram_card)
        left_layout.addWidget(self.disk_card)
        left_layout.addWidget(self.power_card)
        left_layout.addStretch()
        body_layout.addWidget(left_panel, 3)

        # Center Holographic AI Reactor & Voice Activity
        center_panel = QFrame()
        center_panel.setStyleSheet("""
            QFrame {
                background-color: #080D1A;
                border: 1px solid #1E3A8A;
                border-radius: 12px;
                padding: 10px;
            }
            QLabel { border: none; }
        """)
        center_layout = QVBoxLayout(center_panel)
        center_layout.setSpacing(8)
        center_layout.setAlignment(Qt.AlignCenter)

        # Animated Arc Reactor
        self.arc_reactor = ArcReactorWidget()
        center_layout.addWidget(self.arc_reactor, 0, Qt.AlignCenter)

        # Holographic Speech Banner
        self.voice_banner = QLabel("🎤 Say 'Hey JARVIS' or type a command below...")
        self.voice_banner.setAlignment(Qt.AlignCenter)
        self.voice_banner.setStyleSheet("""
            color: #00f0ff;
            background-color: #0F172A;
            border: 1px solid #00f0ff;
            border-radius: 16px;
            padding: 6px 14px;
            font-size: 12px;
            font-family: Consolas, monospace;
        """)
        center_layout.addWidget(self.voice_banner)

        # Holographic Response Box
        self.response_box = QLabel("JARVIS is standing by. All systems nominal.")
        self.response_box.setWordWrap(True)
        self.response_box.setAlignment(Qt.AlignCenter)
        self.response_box.setStyleSheet("""
            color: #E2E8F0;
            background-color: #091322;
            border: 1px dashed #334155;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 12px;
            min-height: 48px;
        """)
        center_layout.addWidget(self.response_box)

        body_layout.addWidget(center_panel, 5)

        # Right HUD Panel: Tactical Commands & Quick Actions
        right_panel = QFrame()
        right_panel.setStyleSheet("""
            QFrame {
                background-color: #0B1322;
                border: 1px solid #1E293B;
                border-right: 3px solid #00f0ff;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton {
                background-color: #0F1E36;
                color: #E2E8F0;
                border: 1px solid #1E3A8A;
                border-radius: 6px;
                padding: 10px;
                text-align: left;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
                border-color: #00f0ff;
                color: #FFFFFF;
            }
            QLabel { border: none; }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(8)

        r_title = QLabel("TACTICAL PROTOCOLS")
        r_title.setStyleSheet("color: #00f0ff; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        right_layout.addWidget(r_title)

        btn_act_weather = QPushButton("🌤️  Current Live Weather")
        btn_act_weather.clicked.connect(lambda: self.action_requested.emit("What is the current weather?"))

        btn_act_vscode = QPushButton("💻  Launch VS Code Editor")
        btn_act_vscode.clicked.connect(lambda: self.action_requested.emit("Open VS Code"))

        btn_act_screen = QPushButton("📸  Capture Screen Diagnostics")
        btn_act_screen.clicked.connect(lambda: self.action_requested.emit("Take a screenshot"))

        btn_act_sys = QPushButton("📊  Full System Health Check")
        btn_act_sys.clicked.connect(lambda: self.action_requested.emit("What is my system memory and CPU usage?"))

        btn_act_notes = QPushButton("📝  Inspect Active Reminders")
        btn_act_notes.clicked.connect(lambda: self.action_requested.emit("List my pending reminders and notes"))

        right_layout.addWidget(btn_act_weather)
        right_layout.addWidget(btn_act_vscode)
        right_layout.addWidget(btn_act_screen)
        right_layout.addWidget(btn_act_sys)
        right_layout.addWidget(btn_act_notes)
        right_layout.addStretch()
        body_layout.addWidget(right_panel, 3)

        main_layout.addLayout(body_layout, 1)

        # 3. Bottom HUD Command Bar (Direct Dashboard Control)
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet("""
            QFrame {
                background-color: #091322;
                border: 1px solid #1E3A8A;
                border-radius: 10px;
                padding: 6px 12px;
            }
        """)
        bot_layout = QHBoxLayout(bottom_bar)
        bot_layout.setSpacing(8)

        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setFixedSize(38, 38)
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background-color: #0F172A;
                color: #00f0ff;
                border: 1px solid #00f0ff;
                border-radius: 19px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #1E293B;
            }
        """)
        self.mic_btn.clicked.connect(self.voice_toggled.emit)
        bot_layout.addWidget(self.mic_btn)

        self.dash_input = QLineEdit()
        self.dash_input.setPlaceholderText("Command JARVIS directly (e.g. 'What's the weather in London?', 'Open Notepad')...")
        self.dash_input.setStyleSheet("""
            QLineEdit {
                background-color: #0B0F17;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #00f0ff;
            }
        """)
        self.dash_input.returnPressed.connect(self._on_dash_send)
        bot_layout.addWidget(self.dash_input, 1)

        send_btn = QPushButton("Execute")
        send_btn.setFixedHeight(38)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: 1px solid #38BDF8;
                border-radius: 8px;
                padding: 0 18px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        send_btn.clicked.connect(self._on_dash_send)
        bot_layout.addWidget(send_btn)

        main_layout.addWidget(bottom_bar)

        # Timers for Clock and Telemetry
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self.update_telemetry)
        self.telemetry_timer.start(2000)
        self.update_telemetry()

        # Update initial weather in background
        QTimer.singleShot(1500, self.update_weather)

    def _update_clock(self) -> None:
        now = datetime.now()
        self.clock_lbl.setText(now.strftime("%H:%M:%S"))

    def _on_dash_send(self) -> None:
        text = self.dash_input.text().strip()
        if text:
            self.dash_input.clear()
            self.set_reactor_state("THINKING", "Processing command")
            self.set_voice_banner(f"User: \"{text}\"")
            self.action_requested.emit(text)

    def set_reactor_state(self, status: str, detail: str = "") -> None:
        self.arc_reactor.set_state(status, detail)

    def set_voice_banner(self, text: str) -> None:
        self.voice_banner.setText(text)

    def set_response_text(self, text: str) -> None:
        self.response_box.setText(text)

    def set_mic_active(self, active: bool) -> None:
        if active:
            self.mic_btn.setStyleSheet("""
                QPushButton {
                    background-color: #DC2626;
                    color: #FFFFFF;
                    border: 2px solid #EF4444;
                    border-radius: 19px;
                    font-size: 15px;
                }
            """)
            self.set_reactor_state("LISTENING", "Microphone Active")
            self.set_voice_banner("🎤 Listening for speech...")
        else:
            self.mic_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0F172A;
                    color: #00f0ff;
                    border: 1px solid #00f0ff;
                    border-radius: 19px;
                    font-size: 15px;
                }
                QPushButton:hover {
                    background-color: #1E293B;
                }
            """)
            self.set_reactor_state("ONLINE", "Idle & Ready")
            self.set_voice_banner("🎤 Say 'Hey JARVIS' or type a command below...")

    def update_weather(self) -> None:
        try:
            res = self.weather_tool.execute(location="auto")
            if res.success and isinstance(res.output, dict):
                temp = res.output.get("temperature_c", "")
                cond = res.output.get("condition", "Clear")
                city = res.output.get("city", "Local")
                self.weather_temp_lbl.setText(f"{temp} • {cond}")
                self.weather_desc_lbl.setText(f"Location: {city}")
            else:
                self.weather_temp_lbl.setText("Weather Ready")
        except Exception:
            self.weather_temp_lbl.setText("Weather Ready")

    def update_telemetry(self) -> None:
        try:
            cpu_pct = int(psutil.cpu_percent(interval=None))
            self.cpu_card.update_value(f"{cpu_pct}%", cpu_pct, "Multi-core load")

            vm = psutil.virtual_memory()
            ram_used_gb = round(vm.used / (1024 ** 3), 1)
            ram_tot_gb = round(vm.total / (1024 ** 3), 1)
            self.ram_card.update_value(f"{ram_used_gb} / {ram_tot_gb} GB", int(vm.percent), f"{vm.percent}% Used")

            disk = psutil.disk_usage("C:\\")
            disk_free_gb = round(disk.free / (1024 ** 3), 1)
            self.disk_card.update_value(f"{disk_free_gb} GB Free", int(disk.percent), f"{disk.percent}% Free Space")

            bat = psutil.sensors_battery()
            if bat:
                status = "Charging" if bat.power_plugged else "Discharging"
                self.power_card.update_value(f"{bat.percent}%", bat.percent, status)
            else:
                self.power_card.update_value("100%", 100, "AC Powered")
        except Exception:
            pass
