"""Main Window integrating all views, asynchronous event runners, and permission modals."""

import asyncio
import time
from typing import Any, Dict, Optional
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.agent.agent import AgentResponse
from app.agent.orchestrator import JarvisOrchestrator
from app.config import Config
from app.constants import RiskLevel
from app.gui.chat import ChatPage
from app.gui.dashboard import DashboardPage
from app.gui.memory import MemoryPage
from app.gui.monitoring import MonitoringPage
from app.gui.settings import SettingsPage
from app.gui.tasks import TasksPage
from app.gui.widgets.confirm_dialog import ConfirmDialog
from app.gui.widgets.sidebar import Sidebar
from app.tools.applications import OpenApplicationTool
from app.tools.system import GetCpuUsageTool, GetCurrentTimeTool, GetMemoryUsageTool
from app.tools.vision import TakeScreenshotTool
from app.tools.weather import GetWeatherTool
from app.utils.logging import get_logger
from app.voice.listener import AudioListener
from app.voice.wakeword import WakeWordDetector

logger = get_logger("gui.main_window")


class WorkerSignals(QObject):
    """Signals for background task execution."""
    finished = Signal(object)
    activity = Signal(str)
    error = Signal(str)


class VoiceBridge(QObject):
    """Bridge for cross-thread voice events."""
    transcription_received = Signal(str)
    listening_state_changed = Signal(bool)


class AsyncWorker(QRunnable):
    """Executes asynchronous coroutine on QThreadPool without blocking Qt UI."""

    def __init__(self, coro_func, *args, **kwargs) -> None:
        super().__init__()
        self.coro_func = coro_func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.coro_func(*self.args, **self.kwargs))
            loop.close()
            self.signals.finished.emit(result)
        except Exception as e:
            logger.error(f"Error in AsyncWorker: {e}")
            self.signals.error.emit(str(e))


class PermissionBridge(QObject):
    """Thread-safe signal bridge for requesting UI permission dialogs."""
    request_confirmation = Signal(str, str, object, dict)


class JarvisMainWindow(QMainWindow):
    """Main application window for JARVIS AI Desktop Agent."""

    def __init__(
        self,
        orchestrator: JarvisOrchestrator,
        audio_listener: Optional[AudioListener] = None,
        wake_detector: Optional[WakeWordDetector] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.audio_listener = audio_listener
        self.wake_detector = wake_detector
        self.config = orchestrator.config
        self.thread_pool = QThreadPool.globalInstance()

        self._is_processing = False
        self._last_active_voice_time = 0.0

        self.setWindowTitle("JARVIS — Holographic AI Desktop Agent")
        self.resize(1180, 760)
        self.setMinimumSize(1000, 650)
        self._apply_dark_theme()

        # Wire confirmation handler
        self.permission_bridge = PermissionBridge()
        self.permission_bridge.request_confirmation.connect(self._show_confirm_dialog, Qt.BlockingQueuedConnection)
        self.orchestrator.permissions.confirmation_callback = self._on_permission_requested

        # Central Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar Navigation
        self.sidebar = Sidebar()
        self.sidebar.page_selected.connect(self._on_page_changed)
        main_layout.addWidget(self.sidebar)

        # Stacked Pages
        self.pages = QStackedWidget()
        self.dashboard_page = DashboardPage(self.config)
        self.chat_page = ChatPage()
        self.tasks_page = TasksPage(self.orchestrator.tasks)
        self.memory_page = MemoryPage(self.orchestrator.memory)
        self.monitoring_page = MonitoringPage()
        self.settings_page = SettingsPage(self.config)

        self.pages.addWidget(self.dashboard_page)  # 0
        self.pages.addWidget(self.chat_page)       # 1
        self.pages.addWidget(self.tasks_page)      # 2
        self.pages.addWidget(self.memory_page)     # 3
        self.pages.addWidget(self.monitoring_page) # 4
        self.pages.addWidget(self.settings_page)   # 5

        main_layout.addWidget(self.pages, 1)

        # Connect inter-page signals
        self.chat_page.message_submitted.connect(self._handle_user_chat_message)
        self.chat_page.voice_toggled.connect(self._toggle_voice_listening)
        self.dashboard_page.action_requested.connect(self._handle_dashboard_action)
        self.dashboard_page.voice_toggled.connect(self._toggle_voice_listening)
        self.tasks_page.task_created.connect(self._handle_task_created)
        self.settings_page.config_saved.connect(self._on_settings_saved)
        self.orchestrator.add_activity_listener(self._on_agent_activity)

        # Voice Bridge Connection
        self.voice_bridge = VoiceBridge()
        self.voice_bridge.transcription_received.connect(self._on_voice_transcription)
        self.voice_bridge.listening_state_changed.connect(self._on_listening_state_changed)

        if self.audio_listener:
            self.audio_listener.on_transcription = self.voice_bridge.transcription_received.emit
            self.audio_listener.on_listening_state = self.voice_bridge.listening_state_changed.emit
            self.audio_listener.on_barge_in = self._on_user_barge_in

    def _on_user_barge_in(self) -> None:
        """Immediately stop JARVIS speech when user speaks over it."""
        if self.orchestrator.tts and self.orchestrator.tts.is_speaking():
            logger.info("User interruption detected: Halting speech output.")
            self.orchestrator.tts.stop()
            self.dashboard_page.set_reactor_state("LISTENING", "User Interrupted")
            self.dashboard_page.set_voice_banner("🎤 Listening to your interruption...")

    def _apply_dark_theme(self) -> None:
        self.setStyleSheet("""
            QMainWindow {
                background-color: #060A12;
            }
            QWidget {
                background-color: #060A12;
                color: #F8FAFC;
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #0B1322;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #1E3A8A;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #00f0ff;
            }
        """)

    def keyPressEvent(self, event) -> None:
        """Allow pressing ESC to instantly halt active speech output."""
        if event.key() == Qt.Key_Escape:
            if self.orchestrator.tts and self.orchestrator.tts.is_speaking():
                logger.info("ESC key pressed: Halting active speech.")
                self.orchestrator.tts.stop()
                self.dashboard_page.set_reactor_state("ONLINE", "Speech Stopped")
                self.dashboard_page.set_voice_banner("Speech stopped by user.")
                return
        super().keyPressEvent(event)

    def _on_page_changed(self, index: int) -> None:
        self.pages.setCurrentIndex(index)

    def _handle_dashboard_action(self, action_text: str) -> None:
        self.dashboard_page.set_voice_banner(f"User: \"{action_text}\"")
        self.dashboard_page.set_reactor_state("THINKING", "Processing command")
        self.chat_page.add_message("You", action_text, is_user=True)
        self._handle_user_chat_message(action_text, speak_response=True)

    def _handle_quick_action(self, action_text: str) -> None:
        self.sidebar.select_page(1)
        self.pages.setCurrentIndex(1)
        self.chat_page.input_field.setText(action_text)
        self.chat_page._on_send()

    def _handle_task_created(self, title: str, desc: str) -> None:
        self.sidebar.select_page(1)
        self.pages.setCurrentIndex(1)
        prompt = f"Please plan and execute the following task: {title}"
        self.chat_page.add_message("You", prompt, is_user=True)
        self._handle_user_chat_message(prompt)

    def _toggle_voice_listening(self) -> None:
        if not self.audio_listener:
            self.dashboard_page.set_response_text("Voice listener is disabled in settings.")
            return

        if self.audio_listener._running:
            self.audio_listener.stop()
            self._on_listening_state_changed(False)
            self.dashboard_page.set_voice_banner("Microphone standby.")
        else:
            self.audio_listener.start()
            self._on_listening_state_changed(True)
            self.dashboard_page.set_voice_banner("🎤 Listening for speech...")

    def _on_listening_state_changed(self, active: bool) -> None:
        self.chat_page.set_mic_active(active)
        self.dashboard_page.set_mic_active(active)

    def _fast_intent_check(self, text: str) -> Optional[str]:
        """Directly execute desktop launch, GPS weather, time, or stats in < 0.1s for instantaneous response."""
        low = text.lower().strip()

        # 1. Instant Hyper-local GPS Weather / Mausam
        if any(p in low for p in ["weather", "mausam", "vedar", "garmi", "sardi", "baarish", "موسم", "بارش", "گرمی", "سردی", "suvidha"]):
            known_cities = {
                "dhamtour": "Dhamtour, Abbottabad", "dhamtaur": "Dhamtour, Abbottabad", "دھمتوڑ": "Dhamtour, Abbottabad",
                "abbottabad": "Abbottabad", "ایبٹ آباد": "Abbottabad",
                "haripur": "Haripur", "ہری پور": "Haripur",
                "lahore": "Lahore", "lahaur": "Lahore", "لاہور": "Lahore",
                "karachi": "Karachi", "کراچی": "Karachi",
                "islamabad": "Islamabad", "اسلام آباد": "Islamabad",
                "rawalpindi": "Rawalpindi", "راولپنڈی": "Rawalpindi",
                "peshawar": "Peshawar", "پشاور": "Peshawar",
                "multan": "Multan", "ملتان": "Multan",
                "faisalabad": "Faisalabad", "فیصل آباد": "Faisalabad",
                "quetta": "Quetta", "کوئٹہ": "Quetta",
                "dubai": "Dubai", "دبئی": "Dubai",
                "london": "London", "لندن": "London",
            }
            target_city = "auto"
            for ck, cv in known_cities.items():
                if ck in low:
                    target_city = cv
                    break

            w_res = GetWeatherTool().execute(location=target_city)
            if w_res.success and isinstance(w_res.output, dict):
                out = w_res.output
                city = out.get("city", "Local Area")
                temp = out.get("temperature_c", "")
                cond = out.get("condition", "Clear")
                hum = out.get("humidity", "")
                is_urdu = any(c in low for c in ["mausam", "garmi", "sardi", "kaisa", "kya", "موسم", "بارش", "گرمی", "vedar", "suvidha"])
                if is_urdu:
                    return f"جی جناب، {city} میں اس وقت موسم {cond} ہے اور درجہ حرارت {temp} ہے۔"
                return f"The current weather in {city} is {cond} at {temp} with {hum} humidity."

        # 2. Instant Real-time Clock / Time
        if any(p in low for p in ["what time", "current time", "what's the time", "today's date", "what date", "time kya", "waqt", "وقت", "ٹائم"]):
            t_res = GetCurrentTimeTool().execute()
            if t_res.success:
                t_str = str(t_res.output)
                is_urdu = any(c in low for c in ["time kya", "waqt", "وقت", "ٹائم"])
                if is_urdu:
                    return f"جی جناب، اس وقت {t_str} کا وقت ہے۔"
                return f"The current system time is {t_str}."

        # 3. Instant CPU & RAM Hardware Usage
        if any(p in low for p in ["cpu usage", "ram usage", "memory usage", "how much ram", "hardware usage", "ram kitni", "cpu kitna", "سسٹم"]):
            m_res = GetMemoryUsageTool().execute()
            c_res = GetCpuUsageTool().execute()
            is_urdu = any(c in low for c in ["ram kitni", "cpu kitna", "سسٹم"])
            if is_urdu:
                return f"آپ کا CPU {c_res.output if c_res.success else ''} اور RAM {m_res.output if m_res.success else ''} استعمال ہو رہا ہے۔"
            return f"Current CPU usage is {c_res.output if c_res.success else 'N/A'}, Memory: {m_res.output if m_res.success else 'N/A'}."

        # 4. Instant VS Code Launch
        if any(p in low for p in ["open vs code", "open the vs code", "launch vs code", "open vscode", "start vs code", "open visual studio code"]):
            res = OpenApplicationTool().execute("vs code")
            reply = "Opening Visual Studio Code for you now."
            if res.success:
                return reply

        # 5. Instant Notepad Launch
        if any(p in low for p in ["open notepad", "launch notepad", "start notepad", "open the notepad"]):
            OpenApplicationTool().execute("notepad")
            return "Opening Notepad for you now."

        # 6. Instant Screenshot Capture
        if any(p in low for p in ["take screenshot", "take a screenshot", "capture screen", "screenshot"]):
            TakeScreenshotTool().execute()
            return "Desktop screenshot captured successfully."

        return None

    def _on_voice_transcription(self, text: str) -> None:
        if not text.strip():
            return

        clean = text.strip()
        logger.info(f"Voice utterance captured: '{clean}'")

        # If user spoke wake word, acknowledge greeting or strip wake word
        if self.wake_detector and self.wake_detector.check_text(clean):
            command = self.wake_detector.strip_wake_word(clean)
            if not command:
                reply = "Yes, I am online and listening. What can I do for you?"
                if self.orchestrator.tts:
                    self.orchestrator.tts.speak(reply)
                self.dashboard_page.set_voice_banner("🎤 'Hey JARVIS' acknowledged.")
                self.dashboard_page.set_response_text(reply)
                self.dashboard_page.set_reactor_state("SPEAKING", "Answering greeting")
                self.chat_page.add_message("JARVIS", reply, is_user=False)
                return
            clean = command

        # Check instantaneous fast desktop action (< 0.1s)
        fast_reply = self._fast_intent_check(clean)
        if fast_reply:
            self.dashboard_page.set_voice_banner(f"Voice Command: \"{clean}\"")
            self.dashboard_page.set_response_text(fast_reply)
            self.dashboard_page.set_reactor_state("ONLINE", "Command Executed")
            self.chat_page.add_message("You (Voice)", clean, is_user=True)
            self.chat_page.add_message("JARVIS", fast_reply, is_user=False)
            if self.orchestrator.tts and self.config.voice.enabled:
                self.orchestrator.tts.speak(fast_reply)
            return

        # Route to AI reasoning engine
        self.dashboard_page.set_voice_banner(f"Voice Command: \"{clean}\"")
        self.dashboard_page.set_reactor_state("THINKING", "Consulting Claude Opus")
        self.chat_page.add_message("You (Voice)", clean, is_user=True)
        self._handle_user_chat_message(clean, speak_response=True)

    def _handle_user_chat_message(self, user_text: str, speak_response: Optional[bool] = None) -> None:
        if self._is_processing:
            logger.debug(f"Skipping overlapping request '{user_text}': Already processing.")
            return

        if speak_response is None:
            speak_response = self.config.voice.enabled

        self._is_processing = True
        self.chat_page.set_status("JARVIS: Thinking...")
        self.dashboard_page.set_reactor_state("THINKING", "Processing with Claude Opus 4.8")

        worker = AsyncWorker(self.orchestrator.handle_user_message, user_text, speak_response=speak_response)
        worker.signals.finished.connect(self._on_message_response)
        worker.signals.error.connect(self._on_message_error)
        self.thread_pool.start(worker)

    def _on_message_response(self, response: AgentResponse) -> None:
        self._is_processing = False
        self._last_active_voice_time = time.time()
        self.chat_page.set_status("")
        self.dashboard_page.set_reactor_state("ONLINE", "Idle & Ready")
        self.dashboard_page.set_response_text(response.content)

        if response.tool_traces:
            for trace in response.tool_traces:
                status_str = "Approved & Done" if trace.approved else "Rejected"
                self.chat_page.add_tool_activity(trace.tool_name, status=status_str, target=str(trace.arguments))

        self.chat_page.add_message("JARVIS", response.content, is_user=False)

    def _on_message_error(self, err_msg: str) -> None:
        self._is_processing = False
        self.chat_page.set_status("")
        self.dashboard_page.set_reactor_state("ONLINE", "Error state")
        self.dashboard_page.set_response_text(f"Error: {err_msg}")
        self.chat_page.add_message("JARVIS", f"I encountered an error: {err_msg}", is_user=False)

    def _on_agent_activity(self, activity_text: str) -> None:
        self.dashboard_page.set_reactor_state("THINKING", activity_text)

    def _on_settings_saved(self, updated_cfg: Config) -> None:
        self.config = updated_cfg
        if self.config.voice.enabled and self.config.voice.wake_word_enabled and self.audio_listener:
            if not self.audio_listener._running:
                self.audio_listener.start()

    def _on_permission_requested(self, tool_name: str, description: str, risk_level: RiskLevel, arguments: Dict[str, Any]) -> bool:
        return self._show_confirm_dialog(tool_name, description, risk_level, arguments)

    def _show_confirm_dialog(self, tool_name: str, description: str, risk_level: RiskLevel, arguments: Dict[str, Any]) -> bool:
        dialog = ConfirmDialog(tool_name, description, risk_level, arguments, self)
        result = dialog.exec()
        return result == ConfirmDialog.Accepted
