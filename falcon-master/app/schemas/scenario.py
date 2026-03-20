from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, field_validator

from app.models import ScenarioStatusEnum
from app.schemas.base import BaseListSchema, BaseQuery, BaseSchema
from app.schemas.response import BaseResponse


class ScenarioCaseBind(BaseModel):
    case_id: int
    order: int
    weight: int


class ScenarioCreate(BaseModel):
    name: str
    project_id: int
    project: str
    description: str | None = None
    cases: List[ScenarioCaseBind] = []


class ScenarioUpdate(BaseModel):
    id: int
    name: str | None = None
    project_id: int | None = None
    project: str | None = None
    description: str | None = None
    cases: Optional[List[ScenarioCaseBind]] = None
    status: ScenarioStatusEnum | None = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value


class QueryScenarioOne(BaseModel):
    id: int


class QueryScenarioList(BaseQuery):
    name: str | None = None
    project_id: int | None = None
    description: str | None = None
    status: ScenarioStatusEnum | None = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value


class ScenarioCaseSummary(BaseModel):
    id: int
    case_id: int
    name: str
    method: str | None = None
    url: str
    status: str
    order: int
    weight: int


class ScenarioCaseDetail(ScenarioCaseSummary):
    type: str
    project_id: int
    project: str
    description: str | None = None
    headers: Any | None = None
    body: str | None = None
    expected_status: str | None = None
    expected_response_time: int | None = None
    assertion: str | None = None
    pre_request_script: str | None = None
    post_request_script: str | None = None
    extract: Any | None = None


class ScenarioInfo(BaseSchema):
    name: str
    project_id: int
    project: str
    status: str
    description: str | None = None
    total_testcases: int = 0
    last_run: datetime | None = None
    cases: List[ScenarioCaseDetail] = []


class ScenarioListItem(BaseSchema):
    name: str
    project_id: int
    project: str
    status: str
    description: str | None = None
    total_testcases: int = 0
    last_run: datetime | None = None
    cases: List[ScenarioCaseSummary] = []


class ScenarioList(BaseListSchema):
    results: List[ScenarioListItem]


class ScenarioListResponse(BaseResponse):
    data: Optional[ScenarioList]


class ScenarioInfoResponse(BaseResponse):
    data: Optional[ScenarioInfo]
