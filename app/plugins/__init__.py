"""Plugin architecture for extending JARVIS capabilities."""

from app.plugins.base import JarvisPlugin
from app.plugins.manager import PluginManager

__all__ = ["JarvisPlugin", "PluginManager"]
