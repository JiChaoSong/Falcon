from enum import Enum


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

    @property
    def label(self) -> str:
        return self.value


class TaskExecutionStrategyEnum(str, Enum):
    SEQUENTIAL = "sequential"
    WEIGHTED = "weighted"


class TaskRunStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
