from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from sqlalchemy import BigInteger, Integer, String, Text, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TaskStatusEnum(str, Enum):
    PENDING = "pending"    # 待执行
    RUNNING = "running"    # 执行中
    COMPLETED = "completed"# 已完成
    FAILED = "failed"      # 执行失败
    CANCELED = "canceled"  # 已取消

    @property
    def label(self):
        labels = {
            self.PENDING: "待执行",
            self.RUNNING: "执行中",
            self.COMPLETED: "已完成",
            self.FAILED: "执行失败",
            self.CANCELED: "已取消",
        }
        return labels[self]


class TaskExecutionStrategyEnum(str, Enum):
    SEQUENTIAL = "sequential"
    WEIGHTED = "weighted"

class Tasks(BaseModel):
    __tablename__ = "tasks"

    name: Mapped[str] = mapped_column(String(100), comment="任务名称，如支付接口压测")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="任务描述")
    owner: Mapped[str] = mapped_column(String(50), nullable=False, comment="任务负责人")
    owner_id: Mapped[int] = mapped_column(BigInteger , nullable=False, comment="任务负责人id")
    project_id:Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属项目id')
    project: Mapped[str] = mapped_column(String(50), nullable=False, comment="所属项目名称")
    status: Mapped[TaskStatusEnum] = mapped_column(
        SQLAlchemyEnum(TaskStatusEnum, name="status"),
        comment="任务状态",
        default=TaskStatusEnum.PENDING
    )
    host: Mapped[Optional[str]] = mapped_column(String(200), nullable=False, comment="压测目标地址，如http://127.0.0.1:8001")
    users:Mapped[int] = mapped_column(Integer, default=10, nullable=False, comment='并发用户数')
    spawn_rate:Mapped[int] = mapped_column(Integer, default=2, nullable=False, comment='生产速率')
    duration:Mapped[int] = mapped_column(Integer, default=60, nullable=False, comment='执行时长,seconds') # seconds
    execution_strategy: Mapped[TaskExecutionStrategyEnum] = mapped_column(
        SQLAlchemyEnum(TaskExecutionStrategyEnum, name="task_execution_strategy"),
        default=TaskExecutionStrategyEnum.SEQUENTIAL,
        nullable=False,
        comment="执行策略",
    )
    finished_at:Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,comment="任务完成时间")
    stats:Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment='统计数据')
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,comment="压测开始时间（对应start_time）")
    runtime_seconds: Mapped[int] = mapped_column(default=0, nullable=True, comment="运行了时长（秒）")
    runtime: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="运行了时长（格式化，如00:00:04）")


class TaskScenario(BaseModel):
    __tablename__ = "task_scenarios"

    task_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="任务id")
    scenario_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="场景id")
    scenario: Mapped[str] = mapped_column(String(100), nullable=False, comment="关联场景名称")
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="执行顺序")
    weight: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="权重")
    target_users: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="目标用户数")
