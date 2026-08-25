"""Filesystem operation tools with safety checks and path validation."""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.constants import RiskLevel
from app.security.sanitizer import InputSanitizer, SecurityViolationError
from app.tools.base import Tool, ToolResult
from app.utils.logging import get_logger

logger = get_logger("tools.filesystem")


class CreateFileTool(Tool):
    name = "create_file"
    description = "Creates a new file at the specified path with optional initial text content."
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Target filepath."},
            "content": {"type": "string", "description": "Initial text content (default empty).", "default": ""},
        },
        "required": ["path"],
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, path: str, content: str = "", **kwargs: Any) -> ToolResult:
        try:
            target = self.sanitizer.validate_path(path, allow_create=True)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return ToolResult(success=True, output=f"Created file '{target}' ({len(content)} characters).")
        except SecurityViolationError as sve:
            return ToolResult(success=False, output="", error=str(sve))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to create file: {e}")


class ReadFileTool(Tool):
    name = "read_file"
    description = "Reads and returns the text contents of a file."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Filepath to read."},
            "max_lines": {"type": "integer", "description": "Maximum number of lines to read (default 500).", "default": 500},
        },
        "required": ["path"],
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, path: str, max_lines: int = 500, **kwargs: Any) -> ToolResult:
        try:
            target = self.sanitizer.validate_path(path)
            if not target.is_file():
                return ToolResult(success=False, output="", error=f"File not found: '{path}'")
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                lines = [f.readline() for _ in range(max_lines)]
                content = "".join(lines)
            return ToolResult(success=True, output=content)
        except SecurityViolationError as sve:
            return ToolResult(success=False, output="", error=str(sve))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to read file: {e}")


class WriteFileTool(Tool):
    name = "write_file"
    description = "Overwrites or creates a file with the provided text content."
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Filepath to write."},
            "content": {"type": "string", "description": "Text content to write."},
        },
        "required": ["path", "content"],
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, path: str, content: str, **kwargs: Any) -> ToolResult:
        try:
            target = self.sanitizer.validate_path(path, allow_create=True)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return ToolResult(success=True, output=f"Successfully wrote {len(content)} characters to '{target}'.")
        except SecurityViolationError as sve:
            return ToolResult(success=False, output="", error=str(sve))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to write file: {e}")


class AppendFileTool(Tool):
    name = "append_file"
    description = "Appends text to the end of an existing file."
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Filepath to append to."},
            "content": {"type": "string", "description": "Text to append."},
        },
        "required": ["path", "content"],
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, path: str, content: str, **kwargs: Any) -> ToolResult:
        try:
            target = self.sanitizer.validate_path(path, allow_create=True)
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "a", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(success=True, output=f"Appended {len(content)} characters to '{target}'.")
        except SecurityViolationError as sve:
            return ToolResult(success=False, output="", error=str(sve))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to append to file: {e}")


class CreateFolderTool(Tool):
    name = "create_folder"
    description = "Creates a directory (and any necessary parent directories)."
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path to create."},
        },
        "required": ["path"],
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, path: str, **kwargs: Any) -> ToolResult:
        try:
            target = self.sanitizer.validate_path(path, allow_create=True)
            target.mkdir(parents=True, exist_ok=True)
            return ToolResult(success=True, output=f"Directory created: '{target}'.")
        except SecurityViolationError as sve:
            return ToolResult(success=False, output="", error=str(sve))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to create directory: {e}")


class ListDirectoryTool(Tool):
    name = "list_directory"
    description = "Lists files and subdirectories inside a given path."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path (default current directory).", "default": "."},
        },
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, path: str = ".", **kwargs: Any) -> ToolResult:
        try:
            target = self.sanitizer.validate_path(path)
            if not target.is_dir():
                return ToolResult(success=False, output="", error=f"Path is not a directory: '{path}'")

            entries = []
            for item in sorted(target.iterdir()):
                kind = "DIR" if item.is_dir() else "FILE"
                size = item.stat().st_size if item.is_file() else "-"
                entries.append(f"[{kind}] {item.name} ({size} bytes)")
            return ToolResult(success=True, output="\n".join(entries) if entries else "(Empty directory)")
        except SecurityViolationError as sve:
            return ToolResult(success=False, output="", error=str(sve))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to list directory: {e}")


class MoveFileTool(Tool):
    name = "move_file"
    description = "Moves a file or folder from source to destination."
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "source": {"type": "string", "description": "Source path."},
            "destination": {"type": "string", "description": "Destination path."},
        },
        "required": ["source", "destination"],
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, source: str, destination: str, **kwargs: Any) -> ToolResult:
        try:
            src = self.sanitizer.validate_path(source)
            dst = self.sanitizer.validate_path(destination, allow_create=True)
            if not src.exists():
                return ToolResult(success=False, output="", error=f"Source path '{source}' does not exist.")
            shutil.move(str(src), str(dst))
            return ToolResult(success=True, output=f"Moved '{src}' to '{dst}'.")
        except SecurityViolationError as sve:
            return ToolResult(success=False, output="", error=str(sve))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to move: {e}")


class CopyFileTool(Tool):
    name = "copy_file"
    description = "Copies a file or folder from source to destination."
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "source": {"type": "string", "description": "Source path."},
            "destination": {"type": "string", "description": "Destination path."},
        },
        "required": ["source", "destination"],
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, source: str, destination: str, **kwargs: Any) -> ToolResult:
        try:
            src = self.sanitizer.validate_path(source)
            dst = self.sanitizer.validate_path(destination, allow_create=True)
            if not src.exists():
                return ToolResult(success=False, output="", error=f"Source path '{source}' does not exist.")
            if src.is_dir():
                shutil.copytree(str(src), str(dst))
            else:
                shutil.copy2(str(src), str(dst))
            return ToolResult(success=True, output=f"Copied '{src}' to '{dst}'.")
        except SecurityViolationError as sve:
            return ToolResult(success=False, output="", error=str(sve))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to copy: {e}")


class RenameFileTool(Tool):
    name = "rename_file"
    description = "Renames a file or folder."
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "old_path": {"type": "string", "description": "Current path."},
            "new_path": {"type": "string", "description": "New path/name."},
        },
        "required": ["old_path", "new_path"],
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, old_path: str, new_path: str, **kwargs: Any) -> ToolResult:
        try:
            src = self.sanitizer.validate_path(old_path)
            dst = self.sanitizer.validate_path(new_path, allow_create=True)
            if not src.exists():
                return ToolResult(success=False, output="", error=f"Path '{old_path}' does not exist.")
            src.rename(dst)
            return ToolResult(success=True, output=f"Renamed '{src}' to '{dst}'.")
        except SecurityViolationError as sve:
            return ToolResult(success=False, output="", error=str(sve))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to rename: {e}")


class DeleteFileTool(Tool):
    name = "delete_file"
    description = "Deletes a file or directory permanently. (HIGH RISK: Requires explicit confirmation)."
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File or folder path to delete."},
        },
        "required": ["path"],
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, path: str, **kwargs: Any) -> ToolResult:
        try:
            target = self.sanitizer.validate_path(path)
            if not target.exists():
                return ToolResult(success=False, output="", error=f"Path '{path}' does not exist.")

            if target.is_dir():
                shutil.rmtree(str(target))
                return ToolResult(success=True, output=f"Deleted directory '{target}'.")
            else:
                target.unlink()
                return ToolResult(success=True, output=f"Deleted file '{target}'.")
        except SecurityViolationError as sve:
            return ToolResult(success=False, output="", error=str(sve))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to delete: {e}")


class SearchFilesTool(Tool):
    name = "search_files"
    description = "Searches for files matching a filename pattern or keyword."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "directory": {"type": "string", "description": "Root directory to search (default '.').", "default": "."},
            "query": {"type": "string", "description": "Filename pattern or substring to match."},
            "max_results": {"type": "integer", "description": "Max results to return (default 20).", "default": 20},
        },
        "required": ["query"],
    }

    def __init__(self, sanitizer: Optional[InputSanitizer] = None) -> None:
        self.sanitizer = sanitizer or InputSanitizer()

    def execute(self, query: str, directory: str = ".", max_results: int = 20, **kwargs: Any) -> ToolResult:
        try:
            target = self.sanitizer.validate_path(directory)
            matches = []
            for root, _, files in os.walk(str(target)):
                for f in files:
                    if query.lower() in f.lower():
                        matches.append(os.path.join(root, f))
                        if len(matches) >= max_results:
                            break
                if len(matches) >= max_results:
                    break
            return ToolResult(success=True, output=matches if matches else f"No files matching '{query}' found.")
        except SecurityViolationError as sve:
            return ToolResult(success=False, output="", error=str(sve))
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to search files: {e}")
