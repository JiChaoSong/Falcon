from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator

from app.models import ProjectPriorityEnum, ProjectStatusEnum
from app.models.project import MemberRoleEnum
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

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value

class ProjectUpdate(BaseModel):
    id: int
    name: str
    description: str | None = None
    status: ProjectStatusEnum | None = None
    priority: ProjectPriorityEnum | None
    tags: list[str] | None = []
    owner_id: int | None = None
    owner_name: str | None = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value

class QueryProjectOne(BaseModel):
    id: int

class QueryProjectList(BaseQuery):
    name: str | None = None
    status: str | None = None
    priority: str | None = None
    tags: List[str] | None = None
    owner_id: int | None = None
    owner_name: str | None = None

    @field_validator("status", "priority", mode="before")
    @classmethod
    def normalize_query_enums(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value


class ProjectMemberCreate(BaseModel):
    project_id: int
    member_id: int
    member_role: MemberRoleEnum

    @field_validator("member_role", mode="before")
    @classmethod
    def normalize_member_role(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value


class ProjectMemberUpdate(BaseModel):
    project_id: int
    member_id: int
    member_role: MemberRoleEnum

    @field_validator("member_role", mode="before")
    @classmethod
    def normalize_member_role(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value


class ProjectMemberRemove(BaseModel):
    project_id: int
    member_id: int


class ProjectMemberInfo(BaseModel):
    id: int
    member_id: int
    member_name: str
    member_role: str
    is_active: bool
    join_time: datetime | None = None


# =============================
# Response Model Schema
# =============================
class ProjectInfo(BaseSchema):
    name: str
    description: str | None = None
    status: str | None = None
    priority: str | None
    tags: list[str] | str | None = None
    owner_id: int
    owner_name: str
    members: list[ProjectMemberInfo] = []

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


class ProjectMemberListResponse(BaseResponse):
    data: Optional[list[ProjectMemberInfo]] = None
