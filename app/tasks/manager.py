"""Task manager tracking long-running operations, planning, and progress."""

from typing import Callable, Dict, List, Optional

from app.constants import TaskStatus
from app.memory.manager import MemoryManager
from app.memory.models import TaskRecord
from app.tasks.models import Task, TaskStep
from app.utils.logging import get_logger

logger = get_logger("tasks.manager")


class TaskManager:
    """Manages active tasks, status transitions, cancellation, and persistence."""

    def __init__(self, memory_manager: Optional[MemoryManager] = None) -> None:
        self.memory = memory_manager
        self.tasks: Dict[str, Task] = {}
        self.listeners: List[Callable[[Task], None]] = []

    def add_listener(self, callback: Callable[[Task], None]) -> None:
        if callback not in self.listeners:
            self.listeners.append(callback)

    def _notify(self, task: Task) -> None:
        for listener in self.listeners:
            try:
                listener(task)
            except Exception as e:
                logger.error(f"Error in task listener: {e}")
        self._persist(task)

    def _persist(self, task: Task) -> None:
        if self.memory:
            record = TaskRecord(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                steps=[s.to_dict() for s in task.steps],
                created_at=task.created_at,
                updated_at=task.updated_at,
            )
            try:
                self.memory.save_task(record)
            except Exception as e:
                logger.error(f"Failed to persist task {task.id}: {e}")

    def create_task(self, title: str, description: str, steps: Optional[List[TaskStep]] = None) -> Task:
        task = Task(title=title, description=description, steps=steps or [])
        self.tasks[task.id] = task
        self._notify(task)
        logger.info(f"Created task [{task.id}]: {title}")
        return task

    def update_status(self, task_id: str, status: TaskStatus) -> Optional[Task]:
        task = self.tasks.get(task_id)
        if task:
            task.status = status.value
            self._notify(task)
            logger.info(f"Task [{task_id}] status -> {status.value}")
            return task
        return None

    def update_step(
        self,
        task_id: str,
        step_index: int,
        status: TaskStatus,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[Task]:
        task = self.tasks.get(task_id)
        if task and 0 <= step_index < len(task.steps):
            step = task.steps[step_index]
            step.status = status.value
            if result:
                step.result = result
            if error:
                step.error = error
            self._notify(task)
            return task
        return None

    def cancel_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if task and task.status in (TaskStatus.PENDING.value, TaskStatus.RUNNING.value, TaskStatus.WAITING_FOR_CONFIRMATION.value):
            task.status = TaskStatus.CANCELLED.value
            self._notify(task)
            logger.info(f"Cancelled task [{task_id}]")
            return True
        return False

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def list_tasks(self) -> List[Task]:
        return list(self.tasks.values())
