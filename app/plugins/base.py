"""Base interface for all JARVIS plugins."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.tools.base import Tool


class JarvisPlugin(ABC):
    """Abstract base class that all loadable plugins must extend."""

    name: str = "base_plugin"
    version: str = "1.0.0"
    description: str = "Base plugin interface."
    author: str = "JARVIS"

    def __init__(self) -> None:
        self.enabled: bool = True

    def initialize(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Called upon plugin load for setup and resource allocation."""
        pass

    def register_tools(self) -> List[Tool]:
        """Return list of tools provided by this plugin."""
        return []

    def shutdown(self) -> None:
        """Called before application exit or plugin unload."""
        pass

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "enabled": self.enabled,
        }
