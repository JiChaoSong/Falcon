from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuntimeContext:
    task_id: int
    task_run_id: int
    host: str
    task_variables: dict[str, Any] = field(default_factory=dict)
    scenario_variables: dict[str, Any] = field(default_factory=dict)

    def render_text(self, value: str | None) -> str | None:
        if value is None:
            return None

        result = value
        variables = {**self.task_variables, **self.scenario_variables}
        for key, item_value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(item_value))
        return result
