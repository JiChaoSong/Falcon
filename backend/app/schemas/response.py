from typing import Any, Optional

from pydantic import BaseModel


class BaseResponse(BaseModel):
    code: Optional[int] = 0
    message: Optional[str] = None
    systemTime: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None
    type: Optional[str] = None
    request_id: Optional[str] = None

class SuccessResponse(BaseResponse):
    data: Optional[Any]

class ErrorResponse(BaseResponse):
    error: str

