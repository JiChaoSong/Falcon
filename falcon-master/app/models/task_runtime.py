from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import BigInteger, DateTime, Enum as SQLAlchemyEnum, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from falcon_shared.runtime_enums import TaskRunStatusEnum


class TaskRun(BaseModel):
    __tablename__ = "task_runs"

    task_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="任务id")
    status: Mapped[TaskRunStatusEnum] = mapped_column(
        SQLAlchemyEnum(TaskRunStatusEnum, name="task_run_status"),
        default=TaskRunStatusEnum.PENDING,
        nullable=False,
        comment="运行状态",
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="开始时间")
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="结束时间")
    runtime_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="运行时长（秒）")
    summary_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="汇总数据")
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="错误信息")


class TaskMetricSecond(BaseModel):
    __tablename__ = "task_metrics_second"

    task_run_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="任务运行id")
    task_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="任务id")
    scenario_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="场景id")
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, comment="指标窗口时间")
    rps: Mapped[float] = mapped_column(Float, default=0, nullable=False, comment="每秒请求数")
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="成功数")
    fail_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="失败数")
    avg_rt: Mapped[float] = mapped_column(Float, default=0, nullable=False, comment="平均响应时间ms")
    p95: Mapped[float] = mapped_column(Float, default=0, nullable=False, comment="P95响应时间ms")
    p99: Mapped[float] = mapped_column(Float, default=0, nullable=False, comment="P99响应时间ms")
    active_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="活跃用户数")
