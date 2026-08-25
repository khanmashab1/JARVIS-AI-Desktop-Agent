# JARVIS Tool Reference

Every capability in JARVIS is represented as a controlled, validated tool. The LLM receives tool schemas and decides which tools to invoke.

## Tool Categories & Risk Levels

| Tool Name | Category | Risk Level | Description |
| :--- | :--- | :--- | :--- |
| `open_application` | Application | `SAFE` | Opens an application (Notepad, VS Code, Calculator, Chrome, etc.) |
| `close_application` | Application | `MEDIUM` | Terminates running application instances |
| `list_running_applications` | Application | `SAFE` | Returns visible desktop application windows |
| `focus_application` | Application | `SAFE` | Focuses and brings a window to the foreground |
| `create_file` | Filesystem | `LOW` | Creates a new text file at path |
| `read_file` | Filesystem | `SAFE` | Reads content from a text file |
| `write_file` | Filesystem | `LOW` | Overwrites or creates file content |
| `append_file` | Filesystem | `LOW` | Appends text to a file |
| `create_folder` | Filesystem | `LOW` | Creates a directory structure |
| `list_directory` | Filesystem | `SAFE` | Lists entries in a directory |
| `move_file` | Filesystem | `MEDIUM` | Moves files or directories |
| `copy_file` | Filesystem | `LOW` | Copies files or directories |
| `rename_file` | Filesystem | `LOW` | Renames a file or directory |
| `delete_file` | Filesystem | `HIGH` | Permanently deletes a file/folder (Requires Confirmation) |
| `search_files` | Filesystem | `SAFE` | Searches for files by name/pattern |
| `get_current_time` | System | `SAFE` | Returns local date, time, and timezone |
| `get_system_information` | System | `SAFE` | Hardware, OS version, processor specs |
| `get_cpu_usage` | System | `SAFE` | Multi-core CPU utilization percentages |
| `get_memory_usage` | System | `SAFE` | Physical RAM and swap memory usage |
| `get_disk_usage` | System | `SAFE` | Total, used, and free disk space |
| `get_battery_status` | System | `SAFE` | Battery percentage, power state |
| `get_network_status` | System | `SAFE` | Network throughput and packets |
| `get_volume` | System | `SAFE` | Master audio output level |
| `set_volume` | System | `SAFE` | Changes system master audio volume (0-100) |
| `open_url` | Browser | `SAFE` | Opens a URL in the browser |
| `search_web` | Browser | `SAFE` | Searches the web and returns snippet results |
| `browser_back` | Browser | `SAFE` | Navigates back in browser history |
| `browser_forward` | Browser | `SAFE` | Navigates forward in browser history |
| `refresh_page` | Browser | `SAFE` | Reloads the active browser page |
| `get_page_title` | Browser | `SAFE` | Returns active page title and URL |
| `get_page_text` | Browser | `SAFE` | Extracts readable text from page |
| `take_screenshot` | Vision | `SAFE` | Captures screen image |
| `save_screenshot` | Vision | `LOW` | Saves desktop screenshot to disk |
| `analyze_screenshot` | Vision | `SAFE` | Visual understanding of active screen |
| `create_note` | Productivity | `LOW` | Stores user note in SQLite |
| `read_note` | Productivity | `SAFE` | Retrieves a note by title or ID |
| `search_notes` | Productivity | `SAFE` | Searches notes by keyword or tags |
| `delete_note` | Productivity | `MEDIUM` | Deletes a stored note |
| `create_reminder` | Productivity | `LOW` | Creates a scheduled reminder |
| `list_reminders` | Productivity | `SAFE` | Lists pending reminders |
| `complete_reminder` | Productivity | `SAFE` | Marks reminder as done |
| `create_project` | Developer | `LOW` | Scaffolds a Python, FastAPI, or CLI project |
| `inspect_project` | Developer | `SAFE` | Analyzes code files, Git, and dependencies |
| `read_source_file` | Developer | `SAFE` | Reads code with line numbering |
| `search_code` | Developer | `SAFE` | Regex/pattern search across source code |
| `run_tests` | Developer | `MEDIUM` | Runs `pytest` in a project directory |
| `get_git_status` | Developer | `SAFE` | Returns branch and modified file status |

## Adding a Custom Tool

To add a new tool:
1. Inherit from `app.tools.base.Tool`.
2. Define `name`, `description`, `parameters` (JSON schema), `risk_level`, and `requires_confirmation`.
3. Implement `execute(**kwargs) -> ToolResult`.
4. Register the tool with `ToolRegistry.register(tool)`.
