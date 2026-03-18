from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class WorkerStatusEnum(str, Enum):
    ONLINE = "online"
    BUSY = "busy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    DISABLED = "disabled"


class WorkerSchedulingStrategyEnum(str, Enum):
    LEAST_LOADED = "least_loaded"
    WEIGHTED = "weighted"
    ROUND_ROBIN = "round_robin"


class Worker(BaseModel):
    __tablename__ = "workers"

    worker_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    host: Mapped[str] = mapped_column(String(100), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    address: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[WorkerStatusEnum] = mapped_column(
        SQLAlchemyEnum(WorkerStatusEnum, name="worker_status"),
        default=WorkerStatusEnum.ONLINE,
        nullable=False,
    )
    capacity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    running_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scheduling_weight: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    tags: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
