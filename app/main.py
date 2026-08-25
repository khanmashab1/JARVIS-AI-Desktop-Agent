"""Application entry point and subsystem orchestrator."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional
from PySide6.QtWidgets import QApplication

from app.agent.orchestrator import JarvisOrchestrator
from app.config import Config
from app.constants import PROJECT_ROOT
from app.gui.main_window import JarvisMainWindow
from app.memory.manager import MemoryManager
from app.plugins.manager import PluginManager
from app.providers.llm.factory import create_llm_provider
from app.providers.stt.whisper import WhisperSTT
from app.providers.tts.factory import create_tts_provider
from app.security.audit import AuditLogger
from app.security.permissions import PermissionEngine
from app.security.policies import SecurityPolicy
from app.security.sanitizer import InputSanitizer
from app.tasks.manager import TaskManager
from app.tasks.scheduler import ReminderScheduler
from app.tools.applications import (
    CloseApplicationTool,
    FocusApplicationTool,
    ListRunningApplicationsTool,
    OpenApplicationTool,
)
from app.tools.browser import (
    BrowserBackTool,
    BrowserForwardTool,
    GetPageTextTool,
    GetPageTitleTool,
    OpenUrlTool,
    RefreshPageTool,
    SearchWebTool,
)
from app.tools.development import (
    CreateProjectTool,
    GetGitStatusTool,
    InspectProjectTool,
    ReadSourceFileTool,
    RunTestsTool,
    SearchCodeTool,
    SuperviseDevTaskTool,
    TestWebsiteTool,
)
from app.tools.filesystem import (
    AppendFileTool,
    CopyFileTool,
    CreateFileTool,
    CreateFolderTool,
    DeleteFileTool,
    ListDirectoryTool,
    MoveFileTool,
    ReadFileTool,
    RenameFileTool,
    SearchFilesTool,
    WriteFileTool,
)
from app.tools.productivity import (
    CompleteReminderTool,
    CreateNoteTool,
    CreateReminderTool,
    DeleteNoteTool,
    ListRemindersTool,
    ReadNoteTool,
    SearchNotesTool,
)
from app.tools.registry import ToolRegistry
from app.tools.system import (
    GetBatteryStatusTool,
    GetCpuUsageTool,
    GetDiskUsageTool,
    GetMemoryUsageTool,
    GetNetworkStatusTool,
    GetSystemInformationTool,
    GetVolumeTool,
    SetVolumeTool,
)
from app.tools.vision import (
    AnalyzeScreenshotTool,
    SaveScreenshotTool,
    TakeScreenshotTool,
)
from app.tools.weather import GetWeatherTool
from app.utils.logging import get_logger, setup_logger
from app.voice.listener import AudioListener
from app.voice.wakeword import WakeWordDetector

logger = get_logger("main")


def initialize_app(config: Config) -> tuple[JarvisOrchestrator, Optional[AudioListener], Optional[WakeWordDetector]]:
    """Instantiate and wire together all subsystems, providers, tools, plugins, and voice pipelines."""
    # 1. Logging
    setup_logger(
        name="jarvis",
        log_file=config.logs_dir / "jarvis.log",
    )
    logger.info("Initializing JARVIS Autonomous Agent subsystems...")

    # 2. Memory & Database
    memory_manager = MemoryManager(config.database_path)

    # 3. Security, Sanitization & Permissions
    policy = SecurityPolicy()
    sanitizer = InputSanitizer(config.security.allowed_filesystem_roots)
    audit_logger = AuditLogger(db_manager=memory_manager.db)
    permission_engine = PermissionEngine(
        policy=policy,
        sanitizer=sanitizer,
        audit_logger=audit_logger,
    )

    # 4. Tool Registry & Core Tools
    registry = ToolRegistry()

    # Application Tools
    registry.register(OpenApplicationTool())
    registry.register(CloseApplicationTool())
    registry.register(ListRunningApplicationsTool())
    registry.register(FocusApplicationTool())

    # Filesystem Tools
    registry.register(CreateFileTool(sanitizer))
    registry.register(ReadFileTool(sanitizer))
    registry.register(WriteFileTool(sanitizer))
    registry.register(AppendFileTool(sanitizer))
    registry.register(CreateFolderTool(sanitizer))
    registry.register(ListDirectoryTool(sanitizer))
    registry.register(MoveFileTool(sanitizer))
    registry.register(CopyFileTool(sanitizer))
    registry.register(RenameFileTool(sanitizer))
    registry.register(DeleteFileTool(sanitizer))
    registry.register(SearchFilesTool(sanitizer))

    # System Diagnostics Tools
    registry.register(GetSystemInformationTool())
    registry.register(GetCpuUsageTool())
    registry.register(GetMemoryUsageTool())
    registry.register(GetDiskUsageTool())
    registry.register(GetBatteryStatusTool())
    registry.register(GetNetworkStatusTool())
    registry.register(GetVolumeTool())
    registry.register(SetVolumeTool())

    # Browser Tools
    registry.register(OpenUrlTool())
    registry.register(SearchWebTool())
    registry.register(BrowserBackTool())
    registry.register(BrowserForwardTool())
    registry.register(RefreshPageTool())
    registry.register(GetPageTitleTool())
    registry.register(GetPageTextTool())

    # Vision Tools
    registry.register(TakeScreenshotTool())
    registry.register(SaveScreenshotTool())
    registry.register(AnalyzeScreenshotTool())

    # Weather & Environmental Tools
    registry.register(GetWeatherTool())

    # Productivity Tools
    registry.register(CreateNoteTool(memory_manager))
    registry.register(ReadNoteTool(memory_manager))
    registry.register(SearchNotesTool(memory_manager))
    registry.register(DeleteNoteTool(memory_manager))
    registry.register(CreateReminderTool(memory_manager))
    registry.register(ListRemindersTool(memory_manager))
    registry.register(CompleteReminderTool(memory_manager))

    # Developer Tools
    registry.register(CreateProjectTool(sanitizer))
    registry.register(InspectProjectTool(sanitizer))
    registry.register(ReadSourceFileTool(sanitizer))
    registry.register(SearchCodeTool(sanitizer))
    registry.register(RunTestsTool(sanitizer))
    registry.register(GetGitStatusTool(sanitizer))
    registry.register(TestWebsiteTool())
    registry.register(SuperviseDevTaskTool(sanitizer))

    # 5. Plugins Subsystem
    plugin_manager = PluginManager(tool_registry=registry)
    plugin_manager.load_all_plugins()

    # 6. Providers
    llm_provider = create_llm_provider(config.llm)
    tts_provider = create_tts_provider(config.voice) if config.voice.enabled else None
    stt_provider = WhisperSTT() if config.voice.enabled else None

    # 7. Task Management & Scheduler
    task_manager = TaskManager(memory_manager=memory_manager)
    scheduler = ReminderScheduler(memory_manager=memory_manager)
    scheduler.start()

    # 8. Orchestrator
    orchestrator = JarvisOrchestrator(
        config=config,
        llm_provider=llm_provider,
        tool_registry=registry,
        permission_engine=permission_engine,
        memory_manager=memory_manager,
        task_manager=task_manager,
        tts_provider=tts_provider,
    )

    # 9. Voice Pipeline (Listener & Wake-Word)
    audio_listener: Optional[AudioListener] = None
    wake_detector: Optional[WakeWordDetector] = None

    if config.voice.enabled and stt_provider:
        wake_detector = WakeWordDetector(wake_phrase=config.voice.wake_word)
        audio_listener = AudioListener(
            stt_provider=stt_provider,
            is_speaking_check=lambda: tts_provider.is_speaking() if tts_provider else False,
        )
        if config.voice.wake_word_enabled:
            audio_listener.start()

    logger.info(f"JARVIS ready with {len(registry.get_enabled_tools())} enabled tools.")
    return orchestrator, audio_listener, wake_detector


def main() -> None:
    """Start the complete desktop application."""
    config = Config.load()
    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    app.setOrganizationName("JARVIS")

    orchestrator, audio_listener, wake_detector = initialize_app(config)
    window = JarvisMainWindow(orchestrator, audio_listener=audio_listener, wake_detector=wake_detector)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
