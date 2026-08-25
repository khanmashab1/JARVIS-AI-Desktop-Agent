"""Plugin Manager coordinating plugin lifecycle and tool registration."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from app.constants import DEFAULT_PLUGINS_DIR
from app.plugins.base import JarvisPlugin
from app.plugins.loader import PluginLoader
from app.tools.registry import ToolRegistry
from app.utils.logging import get_logger

logger = get_logger("plugins.manager")


class PluginManager:
    """Manages loaded plugins, error isolation, and registry integration."""

    def __init__(self, tool_registry: ToolRegistry, plugins_dir: Optional[Path] = None) -> None:
        self.registry = tool_registry
        self.plugins_dir = plugins_dir or DEFAULT_PLUGINS_DIR
        self.plugins: Dict[str, JarvisPlugin] = {}

    def load_all_plugins(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Discover and instantiate all plugins."""
        plugin_classes = PluginLoader.discover_plugins(self.plugins_dir)
        for cls in plugin_classes:
            try:
                plugin_instance = cls()
                plugin_name = plugin_instance.name
                if plugin_name in self.plugins:
                    continue

                plugin_instance.initialize(context)
                self.plugins[plugin_name] = plugin_instance

                # Register tools
                tools = plugin_instance.register_tools()
                for t in tools:
                    self.registry.register(t, enabled=plugin_instance.enabled)

                logger.info(f"Loaded plugin '{plugin_name}' v{plugin_instance.version} with {len(tools)} tool(s).")
            except Exception as e:
                logger.error(f"Failed to initialize plugin class {cls.__name__}: {e}")

    def enable_plugin(self, name: str) -> bool:
        plugin = self.plugins.get(name)
        if plugin:
            plugin.enabled = True
            for t in plugin.register_tools():
                self.registry.set_enabled(t.name, True)
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        plugin = self.plugins.get(name)
        if plugin:
            plugin.enabled = False
            for t in plugin.register_tools():
                self.registry.set_enabled(t.name, False)
            return True
        return False

    def list_plugins(self) -> List[Dict[str, Any]]:
        return [p.get_info() for p in self.plugins.values()]

    def shutdown_all(self) -> None:
        for name, plugin in self.plugins.items():
            try:
                plugin.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down plugin '{name}': {e}")
