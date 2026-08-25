"""Unit tests for TaskManager and Scheduler."""

from pathlib import Path
from app.constants import TaskStatus
from app.memory.manager import MemoryManager
from app.tasks.manager import TaskManager
from app.tasks.models import TaskStep
from app.tasks.scheduler import ReminderScheduler


def test_task_lifecycle_and_progress(tmp_path: Path):
    db_file = tmp_path / "test_tasks.db"
    memory = MemoryManager(db_file)
    manager = TaskManager(memory_manager=memory)

    steps = [
        TaskStep(description="Inspect directory", tool_name="inspect_project"),
        TaskStep(description="Run unit tests", tool_name="run_tests"),
    ]

    task = manager.create_task("Verify Codebase", "Run diagnostics", steps=steps)
    assert task.status == TaskStatus.PENDING.value
    assert task.progress_percent == 0

    # Execute step 1
    manager.update_step(task.id, 0, TaskStatus.COMPLETED, result="Files inspected")
    assert task.progress_percent == 50

    # Execute step 2
    manager.update_step(task.id, 1, TaskStatus.COMPLETED, result="All tests passed")
    manager.update_status(task.id, TaskStatus.COMPLETED)
    assert task.progress_percent == 100
    assert task.status == TaskStatus.COMPLETED.value


def test_task_cancellation(tmp_path: Path):
    manager = TaskManager()
    task = manager.create_task("Long Running Job", "Processing")
    assert manager.cancel_task(task.id) is True
    assert task.status == TaskStatus.CANCELLED.value


def test_reminder_scheduler(tmp_path: Path):
    db_file = tmp_path / "test_sched.db"
    memory = MemoryManager(db_file)

    triggered = []
    def on_rem(rem):
        triggered.append(rem.text)

    scheduler = ReminderScheduler(memory_manager=memory, on_reminder_triggered=on_rem)
    memory.add_reminder("Immediate Task", "now")

    due = scheduler.check_reminders()
    assert len(due) == 1
    assert "Immediate Task" in triggered
