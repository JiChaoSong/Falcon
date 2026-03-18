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

    def render_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.render_text(value)
        if isinstance(value, list):
            return [self.render_value(item) for item in value]
        if isinstance(value, dict):
            return {
                str(self.render_text(str(key))): self.render_value(item)
                for key, item in value.items()
            }
        return value

    def update_variables(self, values: dict[str, Any]) -> None:
        self.scenario_variables.update(values)
