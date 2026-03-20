#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-03 13:51 
    Name  :     request_context.py
    Desc  :     
--------------------------------------
"""
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.decorators.audit import set_current_request_id, get_current_request_id, reset_request_id, get_request_context, \
    set_request_context
import logging
import uuid

logger = logging.getLogger(__name__)



class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # 开始时间
        start_time = time.time()

        # 获取请求基本信息
        method = request.method
        path = request.url.path
        client = f"{request.client.host}:{request.client.port}" if request.client else "unknown"

        # 1. 首先生成并设置 request_id
        request_id = str(uuid.uuid4())
        set_current_request_id(request_id)

        # 2. 获取当前上下文并初始化
        current_context = get_request_context()
        if current_context is None:
            current_context = {}

        # 3. 设置完整的上下文信息
        current_context.update({
            "request_id": request_id,
            "method": method,
            "path": path,
            "client": client,
        })

        # 添加客户端ID（如果有）
        if request.client:
            current_context["client_id"] = f'{request.client.host}:{request.client.port}'
            current_context["client_host"] = request.client.host
            current_context["client_port"] = request.client.port

        # 4. 保存上下文
        set_request_context(current_context)

        # 5. 现在记录第一条日志（此时应该有request_id了）
        logger.info(
            f'请求开始 - {method} {path}',
            extra={
                'method': method,
                'path': path,
                'client': client,
            }
        )

        logger.info(
            f'请求头: - {request.headers}',
            extra={
                'method': method,
                'path': path,
                'client': client,
            }
        )

        try:
            # 处理请求
            response = await call_next(request)

            # 设置响应头
            response.headers["X-Request-Id"] = request_id

            # 计算处理时间
            process_time = time.time() - start_time
            status_code = response.status_code

            # 记录响应日志
            if status_code >= 500:
                logger.error(
                    f"响应完成 - 耗时:{process_time:.3f}s - [状态:{status_code} FAIL]",
                    extra={
                        'method': method,
                        'path': path,
                        'status_code': status_code,
                        'process_time': process_time
                    }
                )
            else:
                logger.info(
                    f"响应完成 - 耗时:{process_time:.3f}s - [状态:{status_code} OK]",
                    extra={
                        'method': method,
                        'path': path,
                        'status_code': status_code,
                        'process_time': process_time
                    }
                )

            return response

        except Exception as e:
            process_time = time.time() - start_time

            # 更新上下文记录错误
            current_context = get_request_context()
            if current_context:
                current_context["error"] = str(e)
                current_context["error_type"] = type(e).__name__
                set_request_context(current_context)

            logger.error(
                f"响应完成 - 耗时:{process_time:.3f}s - [{str(e)}]",
                extra={
                    'method': method,
                    'path': path,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'process_time': process_time
                }
            )
            raise