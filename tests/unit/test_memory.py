"""Unit tests for SQLite database and MemoryManager."""

from pathlib import Path
from app.constants import MemoryType
from app.memory.manager import MemoryManager


def test_memory_crud_and_search(tmp_path: Path):
    db_file = tmp_path / "test_memory.db"
    manager = MemoryManager(db_file)

    # 1. Remember facts
    item1 = manager.remember_project("NEXUS", "NEXUS is an autonomous AI agent architecture.")
    item2 = manager.remember_preference("editor", "User prefers VS Code for Python.")
    item3 = manager.remember_fact("pet", "User has a cat named Luna.")

    all_items = manager.list_memories()
    assert len(all_items) == 3

    # 2. Selective search
    search_nexus = manager.get_relevant_memories("Tell me about my project NEXUS")
    assert len(search_nexus) >= 1
    assert search_nexus[0].key == "NEXUS"

    search_editor = manager.get_relevant_memories("What code editor do I like?")
    assert len(search_editor) >= 1
    assert "VS Code" in search_editor[0].content

    # 3. Forget fact
    manager.delete_memory(item1.id)
    assert len(manager.list_memories()) == 2


def test_conversations_and_messages(tmp_path: Path):
    db_file = tmp_path / "test_chat.db"
    manager = MemoryManager(db_file)

    conv = manager.create_conversation("Unit Test Conversation")
    assert conv.title == "Unit Test Conversation"

    msg1 = manager.add_message(conv.id, "user", "Hello JARVIS")
    msg2 = manager.add_message(conv.id, "assistant", "Greetings! How can I assist?")

    msgs = manager.get_messages(conv.id)
    assert len(msgs) == 2
    assert msgs[0].content == "Hello JARVIS"
    assert msgs[1].content == "Greetings! How can I assist?"


def test_notes_and_reminders(tmp_path: Path):
    db_file = tmp_path / "test_prod.db"
    manager = MemoryManager(db_file)

    # Notes
    note = manager.save_note("Meeting Notes", "Discuss JARVIS architecture with team.", tags=["work", "ai"])
    notes = manager.get_notes()
    assert len(notes) == 1
    assert notes[0].title == "Meeting Notes"

    # Reminders
    rem = manager.add_reminder("Submit report", "2026-08-25T18:00:00")
    rems = manager.list_reminders()
    assert len(rems) == 1
    assert rems[0].completed is False

    manager.complete_reminder(rem.id)
    active_rems = manager.list_reminders(include_completed=False)
    assert len(active_rems) == 0
