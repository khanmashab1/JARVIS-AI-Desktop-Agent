"""High-level Memory Manager coordinating database storage and retrieval."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from app.constants import DEFAULT_DATABASE_PATH, MemoryType
from app.memory.database import DatabaseManager
from app.memory.models import (
    ConversationRecord,
    MemoryItem,
    MessageRecord,
    NoteRecord,
    ReminderRecord,
    TaskRecord,
)
from app.memory.search import MemorySearcher
from app.utils.logging import get_logger

logger = get_logger("memory.manager")


class MemoryManager:
    """Provides memory services to the agent, context builder, and UI."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db = DatabaseManager(db_path or DEFAULT_DATABASE_PATH)
        self.searcher = MemorySearcher()

    # ================= General Memory =================
    def save_memory(
        self,
        key: str,
        content: str,
        memory_type: str = MemoryType.FACT.value,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem:
        """Store or update a piece of information."""
        item = MemoryItem(
            key=key,
            content=content,
            memory_type=memory_type,
            metadata=metadata or {},
        )
        self.db.save_memory(item)
        logger.info(f"Saved memory [{memory_type}]: {key} -> {content}")
        return item

    def delete_memory(self, memory_id_or_key: str) -> bool:
        """Remove a memory by id or key."""
        success = self.db.delete_memory(memory_id_or_key)
        if success:
            logger.info(f"Deleted memory: {memory_id_or_key}")
        return success

    def list_memories(self, memory_type: Optional[str] = None) -> List[MemoryItem]:
        """Return all memories, optionally filtered by type."""
        return self.db.get_all_memories(memory_type)

    def get_relevant_memories(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """Selectively search memories relevant to a query."""
        all_memories = self.db.get_all_memories()
        return self.searcher.search(all_memories, query, limit=limit)

    def remember_fact(self, key: str, fact: str) -> MemoryItem:
        """Convenience method for user facts."""
        return self.save_memory(key=key, content=fact, memory_type=MemoryType.FACT.value)

    def remember_preference(self, key: str, preference: str) -> MemoryItem:
        """Convenience method for user preferences."""
        return self.save_memory(key=key, content=preference, memory_type=MemoryType.PREFERENCE.value)

    def remember_project(self, project_name: str, details: str) -> MemoryItem:
        """Convenience method for project information."""
        return self.save_memory(key=project_name, content=details, memory_type=MemoryType.PROJECT.value)

    # ================= Conversations =================
    def create_conversation(self, title: str = "New Conversation") -> ConversationRecord:
        return self.db.create_conversation(title)

    def list_conversations(self) -> List[ConversationRecord]:
        return self.db.list_conversations()

    def add_message(self, conversation_id: str, role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> MessageRecord:
        return self.db.add_message(conversation_id, role, content, tool_calls)

    def get_messages(self, conversation_id: str, limit: int = 100) -> List[MessageRecord]:
        return self.db.get_messages(conversation_id, limit)

    # ================= Notes =================
    def save_note(self, title: str, content: str, tags: Optional[List[str]] = None) -> NoteRecord:
        note = NoteRecord(title=title, content=content, tags=tags or [])
        self.db.save_note(note)
        return note

    def get_notes(self) -> List[NoteRecord]:
        return self.db.get_notes()

    def delete_note(self, note_id_or_title: str) -> bool:
        return self.db.delete_note(note_id_or_title)

    # ================= Reminders =================
    def add_reminder(self, text: str, due_time: str) -> ReminderRecord:
        rem = ReminderRecord(text=text, due_time=due_time)
        self.db.save_reminder(rem)
        return rem

    def list_reminders(self, include_completed: bool = False) -> List[ReminderRecord]:
        return self.db.get_reminders(include_completed=include_completed)

    def complete_reminder(self, reminder_id: str) -> bool:
        return self.db.complete_reminder(reminder_id)

    # ================= Tasks =================
    def save_task(self, task: TaskRecord) -> None:
        self.db.save_task(task)

    def get_tasks(self, limit: int = 50) -> List[TaskRecord]:
        return self.db.get_tasks(limit)
