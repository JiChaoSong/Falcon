from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel

from app.models import TaskStatusEnum
from app.schemas.base import BaseSchema, BaseListSchema, BaseQuery
from app.schemas.response import BaseResponse


# =============================
# Request Model Schema
# =============================
class TaskScenarioBind(BaseModel):
    scenario_id: int
    order: int = 0


class TaskScenarioInfo(TaskScenarioBind):
    scenario: str


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
    scenarios: List[TaskScenarioBind]

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
    scenarios: Optional[List[TaskScenarioBind]] = None

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

class QueryTaskList(BaseQuery):
    name: str | None = None
    description: str | None = None
    owner_id: int | None = None
    scenario_id: int | None = None
    project_id: int | None = None


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
    status: TaskStatusEnum
    start_time: datetime | None = None
    runtime_seconds: int | None = None
    runtime:str | None = None
    finished_at: datetime | None = None
    stats: Any | None = None
    scenarios: List[TaskScenarioInfo] = []

class TaskList(BaseListSchema):
    results: List[TaskInfo]# 数据列表

class TaskListResponse(BaseResponse):
    data: Optional[TaskList]


class TaskInfoResponse(BaseResponse):
    data: Optional[TaskInfo]
