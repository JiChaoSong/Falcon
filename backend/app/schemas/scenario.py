from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

from app.models import ScenarioStatusEnum
from app.schemas.base import BaseSchema, BaseListSchema, BaseQuery
from app.schemas.case import CaseInfo
from app.schemas.response import BaseResponse


# =============================
# Request Model Schema
# =============================

class ScenarioCaseBind(BaseModel):
    case_id: int
    order: int
    weight: int

class ScenarioCreate(BaseModel):
    name: str
    project_id: int
    project:str
    description:str | None = None
    cases: List[ScenarioCaseBind] = []

class ScenarioUpdate(BaseModel):
    name: str | None = None
    project_id: int | None = None
    project:str | None = None
    description:str | None = None
    cases: Optional[List[ScenarioCaseBind]] = None
    status: ScenarioStatusEnum = None

class QueryScenarioOne(BaseModel):

    id : int

class QueryScenarioList(BaseQuery):
    name: str | None = None
    project_id: int | None = None
    description:str | None = None
    status: ScenarioStatusEnum = None

# =============================
# Response Model Schema
# =============================

class ScenarioInfo(BaseSchema):
    name: str
    project_id: int
    project:str
    status: str
    description:str | None = None
    cases: List[CaseInfo] = []


class ScenarioList(BaseListSchema):

    results: List[ScenarioInfo]# 数据列表


class ScenarioListResponse(BaseResponse):
    data: Optional[ScenarioList]


class ScenarioInfoResponse(BaseResponse):
    data: Optional[ScenarioInfo]