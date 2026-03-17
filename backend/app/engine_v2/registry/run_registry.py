import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class TaskRunControl:
    task_id: int
    task_run_id: int
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    task: asyncio.Task | None = None
    last_snapshot: dict[str, Any] = field(default_factory=dict)
    latest_error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TaskRunRegistry:
    def __init__(self) -> None:
        self._controls: dict[int, TaskRunControl] = {}

    def register(self, control: TaskRunControl) -> None:
        self._controls[control.task_id] = control

    def get(self, task_id: int) -> TaskRunControl | None:
        return self._controls.get(task_id)

    def unregister(self, task_id: int) -> None:
        self._controls.pop(task_id, None)

    def stop(self, task_id: int) -> TaskRunControl | None:
        control = self.get(task_id)
        if control:
            control.cancel_event.set()
        return control


task_run_registry = TaskRunRegistry()
