from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, field_validator

from app.models import WorkerSchedulingStrategyEnum, WorkerStatusEnum
from app.schemas.base import BaseQuery
from app.schemas.response import BaseResponse


class WorkerUpdateRequest(BaseModel):
    worker_id: str
    status: WorkerStatusEnum | None = None
    capacity: int | None = None
    scheduling_weight: int | None = None
    tags: list[str] | None = None
    metadata_json: dict[str, Any] | None = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value


class WorkerQuery(BaseQuery):
    worker_id: str | None = None
    status: WorkerStatusEnum | None = None
    tag: str | None = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value


class WorkerInfoQuery(BaseModel):
    worker_id: str


class WorkerInfo(BaseModel):
    id: int
    worker_id: str
    host: str
    port: int
    address: str
    version: str | None = None
    status: WorkerStatusEnum
    capacity: int
    running_tasks: int
    scheduling_weight: int
    tags: list[str] = []
    metadata_json: dict[str, Any] | None = None
    registered_at: datetime
    last_heartbeat_at: datetime
    last_seen_error: str | None = None
    is_timeout: bool = False
    created_at: datetime
    updated_at: datetime


class WorkerListPayload(BaseModel):
    results: list[WorkerInfo]
    total: int


class WorkerInfoResponse(BaseResponse):
    data: Optional[WorkerInfo]


class WorkerListResponse(BaseResponse):
    data: Optional[WorkerListPayload]

