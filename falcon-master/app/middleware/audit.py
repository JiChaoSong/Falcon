#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-02 12:35
    Name  :     audit_middleware
    Desc  :     
--------------------------------------
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.decorators.audit import with_user_context, get_current_user


class AuditMiddleware(BaseHTTPMiddleware):
    """审计中间件"""

    async def dispatch(self, request: Request, call_next):
        # 从请求中获取用户信息

        # 使用装饰器包装后续处理
        @with_user_context()
        async def _process():
            response = await call_next(request)
            return response

        return await _process()