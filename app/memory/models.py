"""Data models for JARVIS memory, conversations, notes, and tasks."""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.constants import MemoryType, TaskStatus


def generate_uuid() -> str:
    return str(uuid.uuid4())


def current_iso_timestamp() -> str:
    return datetime.now().isoformat()


@dataclass
class MemoryItem:
    """A unit of persistent knowledge (fact, preference, project context)."""
    key: str
    content: str
    memory_type: str = MemoryType.FACT.value
    id: str = field(default_factory=generate_uuid)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=current_iso_timestamp)
    updated_at: str = field(default_factory=current_iso_timestamp)


@dataclass
class MessageRecord:
    """A single chat message in a conversation."""
    role: str
    content: str
    conversation_id: str
    id: str = field(default_factory=generate_uuid)
    tool_calls: Optional[List[Dict[str, Any]]] = None
    created_at: str = field(default_factory=current_iso_timestamp)


@dataclass
class ConversationRecord:
    """A conversation session containing multiple messages."""
    title: str = "New Conversation"
    id: str = field(default_factory=generate_uuid)
    created_at: str = field(default_factory=current_iso_timestamp)
    updated_at: str = field(default_factory=current_iso_timestamp)


@dataclass
class NoteRecord:
    """A user note or snippet."""
    title: str
    content: str
    tags: List[str] = field(default_factory=list)
    id: str = field(default_factory=generate_uuid)
    created_at: str = field(default_factory=current_iso_timestamp)
    updated_at: str = field(default_factory=current_iso_timestamp)


@dataclass
class ReminderRecord:
    """A scheduled task reminder."""
    text: str
    due_time: str
    completed: bool = False
    id: str = field(default_factory=generate_uuid)
    created_at: str = field(default_factory=current_iso_timestamp)


@dataclass
class TaskRecord:
    """A tracked multi-step task."""
    title: str
    description: str
    status: str = TaskStatus.PENDING.value
    steps: List[Dict[str, Any]] = field(default_factory=list)
    id: str = field(default_factory=generate_uuid)
    created_at: str = field(default_factory=current_iso_timestamp)
    updated_at: str = field(default_factory=current_iso_timestamp)
