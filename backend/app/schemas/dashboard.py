from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.models.task import TaskStatusEnum
from app.models.worker import WorkerStatusEnum
from app.schemas.response import BaseResponse


class DashboardOverviewData(BaseModel):
    project_count: int = 0
    case_count: int = 0
    scenario_count: int = 0
    task_count: int = 0
    running_task_count: int = 0
    stopping_task_count: int = 0
    failed_task_count: int = 0
    online_worker_count: int = 0


class DashboardTaskItem(BaseModel):
    id: int
    name: str
    project: str
    host: str | None = None
    users: int = 0
    status: TaskStatusEnum
    runtime: str | None = None
    start_time: datetime | None = None


class DashboardWorkerSummary(BaseModel):
    online: int = 0
    busy: int = 0
    degraded: int = 0
    offline: int = 0


class DashboardWorkerHighlight(BaseModel):
    worker_id: str
    address: str
    status: WorkerStatusEnum
    running_tasks: int = 0
    capacity: int = 0


class DashboardTrendPoint(BaseModel):
    label: str
    task_runs: int = 0
    success_ratio: float = 0
    total_requests: int = 0
    fail_count: int = 0


class DashboardAlertItem(BaseModel):
    level: str
    title: str
    summary: str
    action: str


class DashboardOverviewPayload(BaseModel):
    overview: DashboardOverviewData
    running_tasks: List[DashboardTaskItem] = []
    attention_tasks: List[DashboardTaskItem] = []
    recent_tasks: List[DashboardTaskItem] = []
    worker_summary: DashboardWorkerSummary
    worker_highlights: List[DashboardWorkerHighlight] = []
    today_trend: List[DashboardTrendPoint] = []
    alerts: List[DashboardAlertItem] = []


class DashboardOverviewResponse(BaseResponse):
    data: Optional[DashboardOverviewPayload]
