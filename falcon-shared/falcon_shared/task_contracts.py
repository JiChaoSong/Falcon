import json
from typing import Any

from pydantic import BaseModel, Field


class WorkerExecutionPlanItem(BaseModel):
    scenario: dict[str, Any]
    cases: list[dict[str, Any]] = Field(default_factory=list)
    weight: int = 0
    target_users: int | None = None


class WorkerTaskDefinition(BaseModel):
    task_id: int
    task_run_id: int
    task_name: str
    host: str
    users: int
    spawn_rate: int
    duration: int
    execution_strategy: str
    completion_policy: str = "graceful"
    execution_plan: list[WorkerExecutionPlanItem] = Field(default_factory=list)
    control_plane_addr: str

    def execution_plan_json(self) -> str:
        return json.dumps([item.model_dump(mode="json") for item in self.execution_plan], ensure_ascii=True)

    @staticmethod
    def load_execution_plan_json(raw: str) -> list[WorkerExecutionPlanItem]:
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if not isinstance(parsed, list):
            return []
        return [WorkerExecutionPlanItem.model_validate(item) for item in parsed if isinstance(item, dict)]
