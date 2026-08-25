---
name: jarvis-plugins
description: Use when adding external or optional JARVIS capabilities as plugins (e.g. spotify, github, developer, productivity, study) instead of modifying the core. Covers the JarvisPlugin interface, registering plugin tools through the central registry, startup discovery, and fault isolation so a broken plugin never crashes JARVIS. Triggers include "add plugin", "Spotify support", "integrate GitHub", "extend JARVIS", "new integration". Load with jarvis-core, jarvis-tools, and jarvis-security.
---

# JARVIS Plugins

Plugins extend JARVIS without touching the core agent. New integrations (Spotify, GitHub, etc.) are plugins that contribute tools — they are **not** edits to the agent loop. See jarvis-core.

## Plugin interface

```python
class JarvisPlugin:
    name: str
    version: str
    description: str
    def register_tools(self) -> list[Tool]: ...
```

A plugin's job is to register tools into the central ToolRegistry (jarvis-tools). Those tools carry risk levels and pass through the permission engine like any other (jarvis-security) — plugins get no privileged bypass.

## Layout

```text
plugins/
  spotify/  github/  developer/  productivity/  study/
```

## Discovery

JARVIS discovers and loads *enabled* plugins at startup (driven by configuration). Enabling/disabling is explicit — plugins are not auto-activated without the user's config.

## Fault isolation — critical

A plugin failure must never crash JARVIS. Wrap plugin load and tool execution in error handling: on failure, log it, disable the plugin gracefully, and continue running the rest of the app. One bad plugin degrades only itself.

## Canonical example — "Add Spotify support"

Create `plugins/spotify/` implementing `JarvisPlugin`, register tools like `play_track` / `pause` / `search_music`, assign risk levels, and rely on discovery. **Do not** modify the core agent. This is the pattern for every new integration.

## Definition of done

Plugin implements the interface, registers tools through the registry with risk levels, is discovered from config, is fault-isolated (its errors can't crash JARVIS), and has tests for its tools (see jarvis-testing).
