# JARVIS Plugin System

JARVIS features a modular plugin architecture allowing third-party and custom capabilities to be loaded dynamically from the `plugins/` directory.

## Plugin Structure

A plugin is placed in a subdirectory of `plugins/` containing a `plugin.py` file:

```text
plugins/
  spotify/
    plugin.py
  study/
    plugin.py
  developer/
    plugin.py
  system/
    plugin.py
```

## Plugin Interface

Every plugin inherits from `JarvisPlugin` in `app/plugins/base.py`:

```python
from typing import Any, Dict, List, Optional
from app.plugins.base import JarvisPlugin
from app.tools.base import Tool

class CustomPlugin(JarvisPlugin):
    name = "custom_service"
    version = "1.0.0"
    description = "Extends JARVIS with custom capabilities."
    author = "Developer Name"

    def initialize(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Set up resources, API clients, or database handles."""
        pass

    def register_tools(self) -> List[Tool]:
        """Return list of Tool instances provided by this plugin."""
        return [MyCustomTool()]

    def shutdown(self) -> None:
        """Clean up background threads or open sockets."""
        pass
```

## Built-In Plugins

1. **Study Assistant (`plugins/study/plugin.py`)**:
   - Focus timer / Pomodoro session management.
   - Prolonged eye-closure detection alerts.
   - Looking away / distraction detection.
   - Focus session statistics.

2. **Developer Assistant (`plugins/developer/plugin.py`)**:
   - Project inspection and structure analysis.
   - Safe source code reading and pattern searching.
   - Test execution via `pytest`.
   - Git repository status.

3. **System Manager (`plugins/system/plugin.py`)**:
   - Real-time CPU, RAM, Disk, and Network telemetry.
   - Master volume query and control.
