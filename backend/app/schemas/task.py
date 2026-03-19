from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, field_validator

from app.models import TaskExecutionStrategyEnum, TaskRunStatusEnum, TaskStatusEnum
from app.schemas.base import BaseSchema, BaseListSchema, BaseQuery
from app.schemas.response import BaseResponse


# =============================
# Request Model Schema
# =============================
class TaskScenarioBind(BaseModel):
    scenario_id: int
    order: int = 0
    weight: int = 0
    target_users: int | None = None


class TaskScenarioInfo(TaskScenarioBind):
    scenario: str


class TaskCaseInfo(BaseModel):
    id: int
    name: str
    method: str | None = None
    url: str
    status: str
    order: int = 0
    weight: int = 0


class TaskScenarioDetail(TaskScenarioInfo):
    cases: List[TaskCaseInfo] = []


class TaskCreate(BaseModel):
    name: str
    description: str | None = None
    owner: str
    owner_id: int
    project_id: int
    project: str
    host: str
    users: int
    spawn_rate: int
    duration: int
    execution_strategy: TaskExecutionStrategyEnum = TaskExecutionStrategyEnum.SEQUENTIAL
    scenarios: List[TaskScenarioBind]

    @field_validator("execution_strategy", mode="before")
    @classmethod
    def normalize_execution_strategy(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value

class TaskUpdate(BaseModel):
    id: int
    name: str | None = None
    description: str | None = None
    owner: str | None = None
    owner_id: int | None = None
    project_id: int | None = None
    project: str | None = None
    host: str | None = None
    users: int | None = None
    spawn_rate: int | None = None
    duration: int  | None = None
    execution_strategy: TaskExecutionStrategyEnum | None = None
    scenarios: Optional[List[TaskScenarioBind]] = None
    status: TaskStatusEnum | None = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value

    @field_validator("execution_strategy", mode="before")
    @classmethod
    def normalize_execution_strategy(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value

class TaskRunUpdate(BaseModel):
    id: int
    status: TaskStatusEnum
    start_time: datetime
    runtime_seconds: int
    runtime:str
    finished_at: datetime | None = None
    stats: Any | None = None

class QueryTaskOne(BaseModel):
    id: int


class QueryTaskRuntime(BaseModel):
    task_id: int


class QueryTaskReport(BaseModel):
    task_id: int
    task_run_id: int | None = None


class TaskRunStartRequest(BaseModel):
    task_id: int


class TaskRunStopRequest(BaseModel):
    task_id: int

class QueryTaskList(BaseQuery):
    name: str | None = None
    description: str | None = None
    owner_id: int | None = None
    scenario_id: int | None = None
    project_id: int | None = None
    status: TaskStatusEnum | None = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value


# =============================
# Response Model Schema
# =============================

class TaskInfo(BaseSchema):
    name: str
    description: str | None = None
    owner: str
    owner_id: int
    project_id: int
    project: str
    host: str
    users: int
    spawn_rate: int
    duration: int  | None = None
    execution_strategy: TaskExecutionStrategyEnum = TaskExecutionStrategyEnum.SEQUENTIAL
    status: TaskStatusEnum
    start_time: datetime | None = None
    runtime_seconds: int | None = None
    runtime:str | None = None
    finished_at: datetime | None = None
    stats: Any | None = None
    scenarios: List[TaskScenarioDetail] = []

class TaskList(BaseListSchema):
    results: List[TaskInfo]# 数据列表

class TaskListResponse(BaseResponse):
    data: Optional[TaskList]


class TaskInfoResponse(BaseResponse):
    data: Optional[TaskInfo]


class TaskMetricPoint(BaseModel):
    ts: datetime
    rps: float
    success_count: int
    fail_count: int
    avg_rt: float
    p95: float
    p99: float
    active_users: int


class TaskRuntimeStatusData(BaseModel):
    task_id: int
    task_run_id: int | None = None
    task_name: str
    status: TaskRunStatusEnum | TaskStatusEnum
    started_at: datetime | None = None
    finished_at: datetime | None = None
    runtime_seconds: int = 0
    active_users: int = 0
    total_requests: int = 0
    success_count: int = 0
    fail_count: int = 0
    success_ratio: float = 0
    current_rps: float = 0
    avg_rt: float = 0
    p95: float = 0
    p99: float = 0
    host: str | None = None
    latest_error: str | None = None
    status_code_counts: dict[str, int] = {}
    error_type_counts: dict[str, int] = {}
    failure_samples: List[Any] = []
    stats: List[Any] = []
    history: List[TaskMetricPoint] = []
    worker_snapshot: dict[str, Any] = {}


class TaskRuntimeStatusResponse(BaseResponse):
    data: Optional[TaskRuntimeStatusData]


class TaskRunHistoryItem(BaseModel):
    id: int
    status: TaskRunStatusEnum
    started_at: datetime | None = None
    finished_at: datetime | None = None
    runtime_seconds: int = 0
    total_requests: int = 0
    success_count: int = 0
    fail_count: int = 0
    success_ratio: float = 0
    latest_error: str | None = None


class TaskRunHistoryData(BaseModel):
    task_id: int
    runs: List[TaskRunHistoryItem] = []


class TaskRunHistoryResponse(BaseResponse):
    data: Optional[TaskRunHistoryData]


class TaskReportEndpoint(BaseModel):
    name: str
    method: str
    total_requests: int
    total_failures: int
    avg_response_time: float
    p95: float
    p99: float


class TaskReportData(BaseModel):
    task_id: int
    task_run_id: int | None = None
    task_name: str
    project: str
    owner: str
    host: str
    execution_strategy: TaskExecutionStrategyEnum
    scenario_count: int
    status: TaskRunStatusEnum | TaskStatusEnum
    started_at: datetime | None = None
    finished_at: datetime | None = None
    runtime_seconds: int = 0
    total_requests: int = 0
    success_count: int = 0
    fail_count: int = 0
    success_ratio: float = 0
    avg_rt: float = 0
    p95: float = 0
    p99: float = 0
    latest_error: str | None = None
    status_code_counts: dict[str, int] = {}
    error_type_counts: dict[str, int] = {}
    failure_samples: List[Any] = []
    hottest_endpoint: TaskReportEndpoint | None = None
    riskiest_endpoint: TaskReportEndpoint | None = None
    stats: List[Any] = []
    history: List[TaskMetricPoint] = []
    worker_snapshot: dict[str, Any] = {}


class TaskReportResponse(BaseResponse):
    data: Optional[TaskReportData]
