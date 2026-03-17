from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models import ProjectPriorityEnum, ProjectStatusEnum
from app.schemas.base import BaseSchema, BaseListSchema, BaseQuery
from app.schemas.response import BaseResponse

# =============================
# Request Model Schema
# =============================
class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    priority: ProjectPriorityEnum | None
    tags: list[str] | None = []
    owner_id: int
    owner_name: str

class ProjectUpdate(BaseModel):
    id: int
    name: str
    description: str | None = None
    status: ProjectStatusEnum | None = None
    priority: ProjectPriorityEnum | None
    tags: list[str] | None = []

class QueryProjectOne(BaseModel):
    id: int

class QueryProjectList(BaseQuery):
    name: str | None = None
    status: str | None = None
    priority: str | None
    tags: List[str] | None = None
    owner_id: int | None = None
    owner_name: str | None = None


# =============================
# Response Model Schema
# =============================
class ProjectInfo(BaseSchema):
    name: str
    description: str | None = None
    status: str | None = None
    priority: str | None
    tags: str | None = None
    owner_id: int
    owner_name: str

class ProjectInfoStatistics(ProjectInfo):
    scenario_count: int
    task_count: int
    last_run_time: datetime | None

class ProjectList(BaseListSchema):

    results: List[ProjectInfoStatistics]# 数据列表

class ProjectListResponse(BaseResponse):

    data: ProjectList

class ProjectInfoResponse(BaseResponse):

    data: ProjectInfo