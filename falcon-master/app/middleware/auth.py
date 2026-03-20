#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-03 11:02 
    Name  :     auth.py
    Desc  :     
--------------------------------------
"""
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.response import AuthExceptResponse
from app.core.security import verify_access_token
from fastapi.responses import JSONResponse
import logging

from app.decorators.audit import set_current_user

logger = logging.getLogger(__name__)



class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        path = request.url.path

        # 白名单验证
        if path in settings.AUTH_WHITELIST:
            return await call_next(request)

        # 取token
        token  = request.headers.get("Authorization")
        logger.info(f"请求token:{token}")

        if not token:
            return JSONResponse(content=AuthExceptResponse())

        payload = verify_access_token(token)
        logger.info(f"token信息:{payload}")

        if not payload:
            return JSONResponse(content=AuthExceptResponse())

        set_current_user(payload.id, payload.username)

        # request.state.user = payload

        return await call_next(request)
