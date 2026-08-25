"""Dynamic plugin discovery and importing mechanism."""

import importlib.util
import inspect
from pathlib import Path
from typing import List, Type

from app.plugins.base import JarvisPlugin
from app.utils.logging import get_logger

logger = get_logger("plugins.loader")


class PluginLoader:
    """Discovers and imports plugin classes from filesystem directories."""

    @staticmethod
    def discover_plugins(plugins_dir: Path) -> List[Type[JarvisPlugin]]:
        """Search directories under plugins_dir for subclasses of JarvisPlugin."""
        plugin_classes: List[Type[JarvisPlugin]] = []

        if not plugins_dir.is_dir():
            logger.debug(f"Plugins directory not found: {plugins_dir}")
            return plugin_classes

        for entry in plugins_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith((".", "_")):
                # Check for plugin.py inside subdirectory
                plugin_file = entry / "plugin.py"
                if plugin_file.is_file():
                    classes = PluginLoader._load_classes_from_file(plugin_file)
                    plugin_classes.extend(classes)
            elif entry.is_file() and entry.suffix == ".py" and not entry.name.startswith((".", "_")):
                classes = PluginLoader._load_classes_from_file(entry)
                plugin_classes.extend(classes)

        return plugin_classes

    @staticmethod
    def _load_classes_from_file(file_path: Path) -> List[Type[JarvisPlugin]]:
        found = []
        module_name = f"plugins.{file_path.stem}_{id(file_path)}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, str(file_path))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, JarvisPlugin) and obj is not JarvisPlugin:
                        found.append(obj)
        except Exception as e:
            logger.error(f"Failed to load plugin module from {file_path}: {e}")

        return found
