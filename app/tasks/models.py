"""Task and execution step data models."""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.constants import TaskStatus


def generate_uuid() -> str:
    return str(uuid.uuid4())


def current_iso_timestamp() -> str:
    return datetime.now().isoformat()


@dataclass
class TaskStep:
    """An individual sub-action in a multi-step task."""
    description: str
    tool_name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    status: str = TaskStatus.PENDING.value
    result: Optional[str] = None
    error: Optional[str] = None
    step_id: str = field(default_factory=generate_uuid)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Task:
    """A long-running or multi-step workflow tracked by the system."""
    title: str
    description: str
    status: str = TaskStatus.PENDING.value
    steps: List[TaskStep] = field(default_factory=list)
    id: str = field(default_factory=generate_uuid)
    created_at: str = field(default_factory=current_iso_timestamp)
    updated_at: str = field(default_factory=current_iso_timestamp)

    @property
    def progress_percent(self) -> int:
        if not self.steps:
            return 100 if self.status == TaskStatus.COMPLETED.value else 0
        completed_steps = sum(1 for s in self.steps if s.status == TaskStatus.COMPLETED.value)
        return int((completed_steps / len(self.steps)) * 100)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["progress_percent"] = self.progress_percent
        return d
