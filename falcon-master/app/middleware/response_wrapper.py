#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-03 15:30 
    Name  :     response_wrapper.py
    Desc  :     
--------------------------------------
"""
import json
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.response import SuccessResponse
from app.decorators.audit import get_current_request_id, set_current_user
import logging

logger = logging.getLogger(__name__)

class ResponseWrapperMiddleware(BaseHTTPMiddleware):
    """
    全局响应包装：
    - 自动将返回值包装成 RespModel
    - 自动附加 request_id
    """
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        try:
            # 检查是否需要排除当前路径
            if settings.AUTH_WHITELIST:
                if any(request.url.path.startswith(path) for path in settings.AUTH_WHITELIST):
                    should_wrap = False

            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time

            response.headers["X-Process-Time"] = f"{process_time:.4f}s"

            return response

        except Exception as e:
            logger.error(e)

        finally:
            set_current_user(-1, None)

