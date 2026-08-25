"""Unit tests for the Plugin subsystem."""

from pathlib import Path
from app.constants import DEFAULT_PLUGINS_DIR
from app.plugins.manager import PluginManager
from app.tools.registry import ToolRegistry
from plugins.developer.plugin import DeveloperPlugin
from plugins.study.plugin import StudyPlugin
from plugins.system.plugin import SystemPlugin


def test_plugin_loading_and_tool_registration():
    registry = ToolRegistry()
    manager = PluginManager(tool_registry=registry, plugins_dir=DEFAULT_PLUGINS_DIR)
    manager.load_all_plugins()

    plugins = manager.list_plugins()
    assert len(plugins) >= 3

    plugin_names = [p["name"] for p in plugins]
    assert "study_assistant" in plugin_names
    assert "developer_assistant" in plugin_names
    assert "system_manager" in plugin_names

    # Check tools registered
    assert registry.get("start_focus_timer") is not None
    assert registry.get("create_project") is not None
    assert registry.get("get_cpu_usage") is not None


def test_study_plugin_logic():
    plugin = StudyPlugin()
    plugin.start_session(duration_minutes=15, subject="Algorithms")

    stats = plugin.get_stats()
    assert stats["active_session"] is True
    assert stats["current_subject"] == "Algorithms"
