import datetime
from dataclasses import dataclass
from typing import Any, Dict

from app.decorators.audit import get_current_request_id
from app.enums.base import AbstractBaseCodeMessageEnum
from app.enums.response import ResponseEnums
import logging
logger = logging.getLogger(__name__)

class CommonResponse:

    def __new__(cls, response_enums: AbstractBaseCodeMessageEnum, data: any = None):
        request_id = get_current_request_id().get('request_id')
        response = dict(
            code=response_enums.code,
            message=response_enums.message,
            data=data,
            systemTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            type='success',
            error=None,
            request_id=request_id,
        )
        logger.info(f'响应结果:{response}')
        return response

class SuccessResponse:

    def __new__(cls, data: Any = None, response_enums:AbstractBaseCodeMessageEnum=ResponseEnums.SUCCESS, message: any = None):
        request_id = get_current_request_id().get('request_id')
        response = dict(
                code = response_enums.code,
                message = response_enums.message if message is None else message,
                data = data,
                systemTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                type = 'success',
                error = None,
                request_id=request_id,
        )
        msg = response.copy().pop('message')
        logger.info(f'响应结果:{msg}')

        return response

class SystemExceptionResponse:

    def __new__(cls, response_enums:AbstractBaseCodeMessageEnum=ResponseEnums.SYSTEM_EXCEPTION, exception: any = None):
        request_id = get_current_request_id().get('request_id')
        response = dict(
                code = response_enums.code,
                message = response_enums.message,
                data = None,
                systemTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                type = 'error',
                error=None,
                request_id=request_id,
        )
        logger.info(f'响应结果:{response}')

        return response

class ExceptionResponse:

    def __new__(cls, code, message, exception: Any = None):
        request_id = get_current_request_id().get('request_id')
        response = dict(
            code=code,
            message=message,
            data=None,
            systemTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            type='error',
            error = exception,
            request_id=request_id,

        )
        logger.info(f'响应结果:{response}')

        return response

class AuthExceptResponse:

    def __new__(cls, response_enum:AbstractBaseCodeMessageEnum = ResponseEnums.TOKEN_INVALID, *args, **kwargs):
        request_id = get_current_request_id().get('request_id')
        response = dict(
            code=response_enum.code,
            message=response_enum.message,
            data=None,
            systemTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            type='error',
            error=None,
            request_id=request_id,
        )
        logger.info(f'响应结果:{response}')

        return response

class FailExceptResponse:

    def __new__(cls, message):
        request_id = get_current_request_id().get('request_id')
        response = dict(
            code=42001,
            message=message,
            data=None,
            systemTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            type='error',
            error = None,
            request_id=request_id,
        )
        logger.info(f'响应结果:{response}')

        return response