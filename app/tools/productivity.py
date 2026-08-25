"""Productivity tools for notes, reminders, and user organization."""

from typing import Any, Dict, List, Optional
from app.constants import RiskLevel
from app.memory.manager import MemoryManager
from app.tools.base import Tool, ToolResult
from app.utils.logging import get_logger

logger = get_logger("tools.productivity")


class CreateNoteTool(Tool):
    name = "create_note"
    description = "Saves a new note with a title, body content, and optional tags in SQLite memory."
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Title of the note."},
            "content": {"type": "string", "description": "Body content or snippet."},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional category tags.", "default": []},
        },
        "required": ["title", "content"],
    }

    def __init__(self, memory_manager: Optional[MemoryManager] = None) -> None:
        self.memory = memory_manager or MemoryManager()

    def execute(self, title: str, content: str, tags: Optional[List[str]] = None, **kwargs: Any) -> ToolResult:
        note = self.memory.save_note(title=title, content=content, tags=tags or [])
        return ToolResult(success=True, output=f"Note '{title}' saved successfully with ID {note.id}.")


class ReadNoteTool(Tool):
    name = "read_note"
    description = "Retrieves an existing note by title or identifier."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "title_or_id": {"type": "string", "description": "Note title or ID to retrieve."},
        },
        "required": ["title_or_id"],
    }

    def __init__(self, memory_manager: Optional[MemoryManager] = None) -> None:
        self.memory = memory_manager or MemoryManager()

    def execute(self, title_or_id: str, **kwargs: Any) -> ToolResult:
        notes = self.memory.get_notes()
        target = title_or_id.lower()
        for n in notes:
            if n.id == title_or_id or target in n.title.lower():
                return ToolResult(success=True, output={"title": n.title, "content": n.content, "tags": n.tags, "updated_at": n.updated_at})
        return ToolResult(success=False, output="", error=f"Note '{title_or_id}' not found.")


class SearchNotesTool(Tool):
    name = "search_notes"
    description = "Searches notes for matching keywords in titles, content, or tags."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Keyword to search for in notes."},
        },
        "required": ["query"],
    }

    def __init__(self, memory_manager: Optional[MemoryManager] = None) -> None:
        self.memory = memory_manager or MemoryManager()

    def execute(self, query: str, **kwargs: Any) -> ToolResult:
        notes = self.memory.get_notes()
        q = query.lower()
        matches = []
        for n in notes:
            if q in n.title.lower() or q in n.content.lower() or any(q in t.lower() for t in n.tags):
                matches.append({"id": n.id, "title": n.title, "content": n.content[:150], "tags": n.tags})
        return ToolResult(success=True, output=matches if matches else f"No notes matching '{query}' found.")


class DeleteNoteTool(Tool):
    name = "delete_note"
    description = "Deletes a stored note by title or ID."
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "title_or_id": {"type": "string", "description": "Note title or ID to delete."},
        },
        "required": ["title_or_id"],
    }

    def __init__(self, memory_manager: Optional[MemoryManager] = None) -> None:
        self.memory = memory_manager or MemoryManager()

    def execute(self, title_or_id: str, **kwargs: Any) -> ToolResult:
        ok = self.memory.delete_note(title_or_id)
        if ok:
            return ToolResult(success=True, output=f"Note '{title_or_id}' deleted successfully.")
        return ToolResult(success=False, output="", error=f"Could not find or delete note '{title_or_id}'.")


class CreateReminderTool(Tool):
    name = "create_reminder"
    description = "Schedules a reminder for a specific date/time or duration."
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Reminder text or task message."},
            "due_time": {"type": "string", "description": "ISO timestamp or target time string (e.g. '2026-08-25T20:00:00', '8 PM', 'in 10 minutes')."},
        },
        "required": ["text", "due_time"],
    }

    def __init__(self, memory_manager: Optional[MemoryManager] = None) -> None:
        self.memory = memory_manager or MemoryManager()

    def execute(self, text: str, due_time: str, **kwargs: Any) -> ToolResult:
        rem = self.memory.add_reminder(text=text, due_time=due_time)
        return ToolResult(success=True, output=f"Reminder created for '{due_time}': '{text}' (ID: {rem.id}).")


class ListRemindersTool(Tool):
    name = "list_reminders"
    description = "Lists pending or completed reminders."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "include_completed": {"type": "boolean", "description": "Whether to include finished reminders.", "default": False},
        },
    }

    def __init__(self, memory_manager: Optional[MemoryManager] = None) -> None:
        self.memory = memory_manager or MemoryManager()

    def execute(self, include_completed: bool = False, **kwargs: Any) -> ToolResult:
        rems = self.memory.list_reminders(include_completed=include_completed)
        out = [{"id": r.id, "text": r.text, "due_time": r.due_time, "completed": r.completed} for r in rems]
        return ToolResult(success=True, output=out if out else "No pending reminders.")


class CompleteReminderTool(Tool):
    name = "complete_reminder"
    description = "Marks a reminder as completed."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "reminder_id": {"type": "string", "description": "ID or text substring of the reminder to complete."},
        },
        "required": ["reminder_id"],
    }

    def __init__(self, memory_manager: Optional[MemoryManager] = None) -> None:
        self.memory = memory_manager or MemoryManager()

    def execute(self, reminder_id: str, **kwargs: Any) -> ToolResult:
        ok = self.memory.complete_reminder(reminder_id)
        if ok:
            return ToolResult(success=True, output=f"Reminder '{reminder_id}' marked as completed.")
        return ToolResult(success=False, output="", error=f"Reminder '{reminder_id}' not found.")
