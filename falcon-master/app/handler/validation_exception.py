#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-04 11:07
    Name  :     validation_exception
    Desc  :     
--------------------------------------
"""
import datetime
import json
from json import JSONDecodeError

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.exception import ParamException, TokenException
from app.core.response import SuccessResponse, ExceptionResponse, AuthExceptResponse
import logging
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)

def register_validation_exception_handler(app: FastAPI):

    # 处理请求验证错误（FastAPI 默认会捕获，但可以自定义）
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = {}
        for err in exc.errors():
            field = err["loc"][-1]  # 提取字段名
            # 获取中文提示（无匹配则用原英文）
            msg = settings.ERROR_MSG_MAP.get(err["type"], err["msg"])

            # 同一字段多个错误合并（分号分隔）
            if field in errors:
                errors[field] += f"；{msg}"
            else:
                errors[field] = msg
        return JSONResponse(
            status_code=200,
            content=ExceptionResponse(
                code=40021,
                message="数据验证失败",
                exception=errors
            ),
        )

    @app.exception_handler(JSONDecodeError)
    async def json_decode_exception_handler(request: Request, exc: JSONDecodeError):

        return JSONResponse(content=ExceptionResponse(
            code=40021,
            message='参数错误',
            exception= f"格式错误，位置:{exc.pos}，描述:{exc.msg}",
        ))

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(content=ExceptionResponse(
            code=40024,
            message=str(exc.detail),
            exception= f'{exc.detail}, path: {request.url.path}',
        ))

    # 自定义异常处理器（中英文双提示）
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        errors = {}
        for err in exc.errors():
            field = err["loc"][-1]  # 提取字段名
            # 获取中文提示（无匹配则用原英文）
            msg = settings.ERROR_MSG_MAP.get(err["type"], err["msg"])

            # 同一字段多个错误合并（分号分隔）
            if field in errors:
                errors[field] += f"；{msg}"
            else:
                errors[field] = msg
        return JSONResponse(
            status_code=200,
            content=ExceptionResponse(
                code=40021,
                message="数据验证失败",
                exception=errors
            ),
        )

    @app.exception_handler(TypeError)
    async def type_exception_handler(request: Request, exc: TypeError):

        return JSONResponse(content=ExceptionResponse(
            code=40023,
            message='参数类型错误',
            exception= f"{exc}",
        ))

    @app.exception_handler(TokenException)
    async def token_exception_handler(request: Request, exc: TokenException):
        return JSONResponse(content=AuthExceptResponse())

    @app.exception_handler(ParamException)
    async def param_exception_handler(request: Request, exc: ParamException):
        return JSONResponse(content=ExceptionResponse(
            code=40025,
            message=str(exc),
            exception= 'error',
        ))

    @app.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
        return JSONResponse(content=ExceptionResponse(
            code=40020,
            message='未知错误',
            exception= str(exc),
        ))