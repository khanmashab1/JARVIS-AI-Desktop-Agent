"""Task planning and decomposition engine."""

from typing import Any, Dict, List, Optional
from app.tasks.models import Task, TaskStep
from app.utils.logging import get_logger

logger = get_logger("agent.planner")


class Planner:
    """Decomposes complex goals into manageable steps."""

    @staticmethod
    def create_plan_from_steps(title: str, description: str, steps_data: List[Dict[str, Any]]) -> Task:
        steps = []
        for s in steps_data:
            steps.append(
                TaskStep(
                    description=s.get("description", "Step"),
                    tool_name=s.get("tool_name", ""),
                    arguments=s.get("arguments", {}),
                )
            )
        return Task(title=title, description=description, steps=steps)
