"""SQLite database manager for JARVIS persistence."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.memory.models import (
    ConversationRecord,
    MemoryItem,
    MessageRecord,
    NoteRecord,
    ReminderRecord,
    TaskRecord,
)
from app.utils.logging import get_logger

logger = get_logger("memory.database")


class DatabaseManager:
    """Manages SQLite connection, schema migrations, and queries."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for improved concurrency
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_schema(self) -> None:
        """Create database tables if they do not exist."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tool_calls TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            memory_type TEXT NOT NULL,
            key TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            steps TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reminders (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            due_time TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tool_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            arguments TEXT,
            approved INTEGER NOT NULL,
            reason TEXT,
            status TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
        with self._get_connection() as conn:
            conn.executescript(schema_sql)
            conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    # ================= Conversations & Messages =================
    def create_conversation(self, title: str = "New Conversation") -> ConversationRecord:
        record = ConversationRecord(title=title)
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (record.id, record.title, record.created_at, record.updated_at),
            )
            conn.commit()
        return record

    def list_conversations(self, limit: int = 50) -> List[ConversationRecord]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                ConversationRecord(
                    id=row["id"],
                    title=row["title"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    def add_message(self, conversation_id: str, role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> MessageRecord:
        record = MessageRecord(
            role=role,
            content=content,
            conversation_id=conversation_id,
            tool_calls=tool_calls,
        )
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO messages (id, conversation_id, role, content, tool_calls, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    record.id,
                    record.conversation_id,
                    record.role,
                    record.content,
                    json.dumps(record.tool_calls) if record.tool_calls else None,
                    record.created_at,
                ),
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (record.created_at, conversation_id),
            )
            conn.commit()
        return record

    def get_messages(self, conversation_id: str, limit: int = 100) -> List[MessageRecord]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT id, conversation_id, role, content, tool_calls, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ?",
                (conversation_id, limit),
            ).fetchall()
            messages = []
            for row in rows:
                tc = json.loads(row["tool_calls"]) if row["tool_calls"] else None
                messages.append(
                    MessageRecord(
                        id=row["id"],
                        conversation_id=row["conversation_id"],
                        role=row["role"],
                        content=row["content"],
                        tool_calls=tc,
                        created_at=row["created_at"],
                    )
                )
            return messages

    # ================= Memories =================
    def save_memory(self, memory: MemoryItem) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO memories (id, memory_type, key, content, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    memory_type=excluded.memory_type,
                    key=excluded.key,
                    content=excluded.content,
                    metadata=excluded.metadata,
                    updated_at=excluded.updated_at
                """,
                (
                    memory.id,
                    memory.memory_type,
                    memory.key,
                    memory.content,
                    json.dumps(memory.metadata),
                    memory.created_at,
                    memory.updated_at,
                ),
            )
            conn.commit()

    def get_all_memories(self, memory_type: Optional[str] = None) -> List[MemoryItem]:
        with self._get_connection() as conn:
            if memory_type:
                rows = conn.execute(
                    "SELECT id, memory_type, key, content, metadata, created_at, updated_at FROM memories WHERE memory_type = ? ORDER BY updated_at DESC",
                    (memory_type,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, memory_type, key, content, metadata, created_at, updated_at FROM memories ORDER BY updated_at DESC"
                ).fetchall()

            items = []
            for r in rows:
                meta = json.loads(r["metadata"]) if r["metadata"] else {}
                items.append(
                    MemoryItem(
                        id=r["id"],
                        memory_type=r["memory_type"],
                        key=r["key"],
                        content=r["content"],
                        metadata=meta,
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                    )
                )
            return items

    def delete_memory(self, memory_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM memories WHERE id = ? OR key = ?", (memory_id, memory_id))
            conn.commit()
            return cursor.rowcount > 0

    # ================= Notes =================
    def save_note(self, note: NoteRecord) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO notes (id, title, content, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    content=excluded.content,
                    tags=excluded.tags,
                    updated_at=excluded.updated_at
                """,
                (
                    note.id,
                    note.title,
                    note.content,
                    json.dumps(note.tags),
                    note.created_at,
                    note.updated_at,
                ),
            )
            conn.commit()

    def get_notes(self) -> List[NoteRecord]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT id, title, content, tags, created_at, updated_at FROM notes ORDER BY updated_at DESC").fetchall()
            notes = []
            for r in rows:
                t = json.loads(r["tags"]) if r["tags"] else []
                notes.append(
                    NoteRecord(
                        id=r["id"],
                        title=r["title"],
                        content=r["content"],
                        tags=t,
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                    )
                )
            return notes

    def delete_note(self, note_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM notes WHERE id = ? OR title = ?", (note_id, note_id))
            conn.commit()
            return cursor.rowcount > 0

    # ================= Reminders =================
    def save_reminder(self, reminder: ReminderRecord) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO reminders (id, text, due_time, completed, created_at) VALUES (?, ?, ?, ?, ?)",
                (reminder.id, reminder.text, reminder.due_time, 1 if reminder.completed else 0, reminder.created_at),
            )
            conn.commit()

    def get_reminders(self, include_completed: bool = False) -> List[ReminderRecord]:
        with self._get_connection() as conn:
            query = "SELECT id, text, due_time, completed, created_at FROM reminders"
            if not include_completed:
                query += " WHERE completed = 0"
            query += " ORDER BY due_time ASC"
            rows = conn.execute(query).fetchall()
            return [
                ReminderRecord(
                    id=r["id"],
                    text=r["text"],
                    due_time=r["due_time"],
                    completed=bool(r["completed"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def complete_reminder(self, reminder_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("UPDATE reminders SET completed = 1 WHERE id = ? OR text LIKE ?", (reminder_id, f"%{reminder_id}%"))
            conn.commit()
            return cursor.rowcount > 0

    # ================= Tasks =================
    def save_task(self, task: TaskRecord) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO tasks (id, title, description, status, steps, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    description=excluded.description,
                    status=excluded.status,
                    steps=excluded.steps,
                    updated_at=excluded.updated_at
                """,
                (
                    task.id,
                    task.title,
                    task.description,
                    task.status,
                    json.dumps(task.steps),
                    task.created_at,
                    task.updated_at,
                ),
            )
            conn.commit()

    def get_tasks(self, limit: int = 50) -> List[TaskRecord]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT id, title, description, status, steps, created_at, updated_at FROM tasks ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
            tasks = []
            for r in rows:
                st = json.loads(r["steps"]) if r["steps"] else []
                tasks.append(
                    TaskRecord(
                        id=r["id"],
                        title=r["title"],
                        description=r["description"],
                        status=r["status"],
                        steps=st,
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                    )
                )
            return tasks

    # ================= Audit Logs =================
    def save_audit_record(self, record: Any) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO tool_logs (timestamp, tool_name, risk_level, arguments, approved, reason, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    record.timestamp,
                    record.tool_name,
                    record.risk_level,
                    json.dumps(record.arguments) if isinstance(record.arguments, dict) else str(record.arguments),
                    1 if record.approved else 0,
                    record.reason,
                    record.status,
                ),
            )
            conn.commit()
