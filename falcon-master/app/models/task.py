from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import BigInteger, DateTime, Enum as SQLAlchemyEnum, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from falcon_shared.runtime_enums import TaskExecutionStrategyEnum, TaskStatusEnum


class Tasks(BaseModel):
    __tablename__ = "tasks"

    name: Mapped[str] = mapped_column(String(100), comment="task name")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="task description")
    owner: Mapped[str] = mapped_column(String(50), nullable=False, comment="task owner")
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="task owner id")
    project_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="project id")
    project: Mapped[str] = mapped_column(String(50), nullable=False, comment="project name")
    status: Mapped[TaskStatusEnum] = mapped_column(
        SQLAlchemyEnum(TaskStatusEnum, name="status"),
        comment="task status",
        default=TaskStatusEnum.PENDING,
    )
    host: Mapped[Optional[str]] = mapped_column(String(200), nullable=False, comment="target host")
    users: Mapped[int] = mapped_column(Integer, default=10, nullable=False, comment="virtual users")
    spawn_rate: Mapped[int] = mapped_column(Integer, default=2, nullable=False, comment="spawn rate")
    duration: Mapped[int] = mapped_column(Integer, default=60, nullable=False, comment="duration seconds")
    execution_strategy: Mapped[TaskExecutionStrategyEnum] = mapped_column(
        SQLAlchemyEnum(TaskExecutionStrategyEnum, name="task_execution_strategy"),
        default=TaskExecutionStrategyEnum.SEQUENTIAL,
        nullable=False,
        comment="execution strategy",
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="task finished time",
    )
    stats: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="task stats")
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="task start time",
    )
    runtime_seconds: Mapped[int] = mapped_column(default=0, nullable=True, comment="runtime seconds")
    runtime: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="formatted runtime")


class TaskScenario(BaseModel):
    __tablename__ = "task_scenarios"

    task_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="task id")
    scenario_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="scenario id")
    scenario: Mapped[str] = mapped_column(String(100), nullable=False, comment="scenario name")
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="execution order")
    weight: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="weight")
    target_users: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="target users")
