from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Any

from app.models import CaseStatusEnum
from app.schemas.base import BaseSchema, BaseListSchema, BaseQuery
from app.schemas.response import BaseResponse


# =============================
# Request Model Schema
# =============================

class CaseCreate(BaseModel):

    name: str
    type: str
    project_id: int
    project: str
    method: str
    url: str
    description: str | None = None


class CaseUpdate(BaseModel):
    name: Optional[str] = None
    method: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[dict] = None
    body: Optional[dict] = None
    status: Optional[CaseStatusEnum] = None

class QueryCaseOne(BaseModel):
    id: int

class QueryCaseList(BaseQuery):

    name: str | None = None
    project_id: int | None = None
    type: str | None = None
    method: str | None = None
    url: str | None = None

class CaseConfig(BaseModel):
    id: int
    headers: Any | None = None
    body: str | None = None
    expected_status: str | None = None
    expected_response_time: int | None = None
    assertion: str | None = None
    pre_request_script: str | None = None
    post_request_script: str | None = None
    extract: Any | None = None

# =============================
# Response Model Schema
# =============================
class CaseInfo(BaseSchema):
    name: str
    type: str
    project_id: int
    project: str
    method: str
    url: str
    status: str
    description: str | None = None
    headers: Any | None = None
    body: str | None = None
    expected_status: str | None = None
    expected_response_time: int | None = None
    assertion: str | None = None
    pre_request_script: str | None = None
    post_request_script: str | None = None
    extract: Any | None = None

class CaseList(BaseListSchema):

    results: List[CaseInfo]# 数据列表

class CaseListResponse(BaseResponse):

    data: Optional[CaseList]

class CaseInfoResponse(BaseResponse):

    data: Optional[CaseInfo]