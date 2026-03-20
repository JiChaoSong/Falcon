from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator
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
    id: int
    name: Optional[str] = None
    type: Optional[str] = None
    project_id: Optional[int] = None
    project: Optional[str] = None
    method: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    headers: Optional[dict] = None
    body: Optional[dict] = None
    status: Optional[CaseStatusEnum] = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value

class QueryCaseOne(BaseModel):
    id: int

class QueryCaseList(BaseQuery):

    name: str | None = None
    project_id: int | None = None
    type: str | None = None
    method: str | None = None
    url: str | None = None
    status: CaseStatusEnum | None = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value

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


class CaseImportSourceEnum(str, Enum):
    OPENAPI_URL = "openapi_url"
    OPENAPI_JSON = "openapi_json"


class CaseImportConflictPolicyEnum(str, Enum):
    SKIP = "skip"
    OVERWRITE = "overwrite"


class CaseImportPreviewRequest(BaseModel):
    project_id: int
    source_type: CaseImportSourceEnum
    source_url: str | None = None
    document_content: str | None = None


class CaseImportItem(BaseModel):
    name: str
    method: str
    url: str
    description: str | None = None
    tags: List[str] = Field(default_factory=list)
    headers: List[dict[str, str]] = Field(default_factory=list)
    body: str | None = None
    expected_status: str | None = None
    exists: bool = False
    duplicate_case_id: int | None = None
    duplicate_case_name: str | None = None


class CaseImportPreviewData(BaseModel):
    project_id: int
    project_name: str
    source_type: CaseImportSourceEnum
    total_count: int
    duplicate_count: int
    importable_count: int
    results: List[CaseImportItem]


class CaseImportPreviewResponse(BaseResponse):
    data: Optional[CaseImportPreviewData]


class CaseImportCommitRequest(BaseModel):
    project_id: int
    source_type: CaseImportSourceEnum
    source_url: str | None = None
    document_content: str | None = None
    items: List[CaseImportItem]
    conflict_policy: CaseImportConflictPolicyEnum = CaseImportConflictPolicyEnum.SKIP
    default_status: CaseStatusEnum = CaseStatusEnum.DRAFT

    @field_validator("default_status", mode="before")
    @classmethod
    def normalize_default_status(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value


class CaseImportCommitData(BaseModel):
    project_id: int
    project_name: str
    created_count: int
    updated_count: int
    skipped_count: int
    failed_count: int
    created_case_ids: List[int] = Field(default_factory=list)
    failed_items: List[dict[str, str]] = Field(default_factory=list)


class CaseImportCommitResponse(BaseResponse):
    data: Optional[CaseImportCommitData]

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
