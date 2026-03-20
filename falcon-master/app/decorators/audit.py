#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-02 12:28
    Name  :     model_decorators
    Desc  :     
--------------------------------------
"""
import threading
import uuid
from contextvars import ContextVar
from typing import Optional, Callable, Tuple, Dict, Any
from functools import wraps
from typing import Callable, TypeVar
import asyncio

T = TypeVar('T')


_current_user_local = threading.local()

_current_user_id: ContextVar[Optional[int]] = ContextVar('id', default=None)
_current_user_name: ContextVar[Optional[str]] = ContextVar("username", default=None)
_current_request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
_request_context_ctx: ContextVar[Optional[Dict[str, Any]]] = ContextVar("request_context", default=None)


def get_current_user() -> Tuple[Optional[int], Optional[str]]:
    return _current_user_id.get(), _current_user_name.get()


def set_current_user(user_id: int, user_name: str):
    t1 = _current_user_id.set(user_id)
    t2 = _current_user_name.set(user_name)
    return t1, t2


def reset_user(tokens):
    t1, t2 = tokens
    _current_user_id.reset(t1)
    _current_user_name.reset(t2)

def get_current_request_id():
    return {
        'request_id': _current_request_id.get()
    }

def set_current_request_id(request_id:Optional[str] = None):
    return _current_request_id.set(request_id or str(uuid.uuid4()))

def reset_request_id(tokens):
    _current_request_id.reset(tokens[0])


def get_request_context() -> Optional[Dict[str, Any]]:
    """获取当前请求上下文"""
    return _request_context_ctx.get()

def set_request_context(context: Dict[str, Any]):
    _request_context_ctx.set(context)

class CurrentUserContext:
    """当前用户上下文管理器"""

    def __init__(self, user_id=None, user_name=None):
        self.user_id = user_id
        self.user_name = user_name

    def __enter__(self):
        # 设置线程局部变量
        _current_user_local.user_id = self.user_id
        _current_user_local.user_name = self.user_name

        # 设置 contextvars
        if self.user_id is not None:
            self._token_id = _current_user_id.set(self.user_id)
        if self.user_name is not None:
            self._token_name = _current_user_name.set(self.user_name)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 清理线程局部变量
        if hasattr(_current_user_local, 'user_id'):
            delattr(_current_user_local, 'user_id')
        if hasattr(_current_user_local, 'user_name'):
            delattr(_current_user_local, 'user_name')


# 快捷装饰器，用于包装函数自动设置用户上下文
def with_user_context():
    """用户上下文装饰器"""
    user_id, user_name = get_current_user()

    def decorator(func):
        def wrapper(*args, **kwargs):
            with CurrentUserContext(user_id, user_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def with_request_context(func: Callable[..., T]) -> Callable[..., T]:
    """装饰器：为函数提供请求上下文访问"""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # 在异步函数中访问上下文
        request_context = get_request_context()
        if request_context:
            # 将请求上下文作为关键字参数传递给函数（如果函数接受）
            kwargs["request_context"] = request_context
        return await func(*args, **kwargs)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        # 在同步函数中访问上下文
        request_context = get_request_context()
        if request_context:
            kwargs["request_context"] = request_context
        return func(*args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


# 可选：创建全局可访问的请求上下文管理器
class RequestContextManager:
    """请求上下文管理器（便于在任意位置访问）"""

    @staticmethod
    def get_request_id() -> Optional[str]:
        return _current_request_id.get()

    @staticmethod
    def get_context() -> Optional[Dict[str, Any]]:
        return get_request_context()

    @staticmethod
    def set_context_value(key: str, value: Any):
        """在请求上下文中设置自定义值"""
        current_context = get_request_context()
        if current_context:
            current_context[key] = value
            _request_context_ctx.set(current_context)

    @staticmethod
    def get_context_value(key: str, default: Any = None) -> Any:
        """从请求上下文中获取值"""
        current_context = get_request_context()
        if current_context:
            return current_context.get(key, default)
        return default


# 为方便使用，创建全局实例
request_context = RequestContextManager()