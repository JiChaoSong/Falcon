import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class TaskRunControl:
    task_id: int
    task_run_id: int
    cancel_event: threading.Event = field(default_factory=threading.Event)
    task: threading.Thread | None = None
    last_snapshot: dict[str, Any] = field(default_factory=dict)
    latest_error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
