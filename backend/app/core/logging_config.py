# !/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-03 13:33
    Name  :     logging_config.py
    Desc  :     日志配置模块
--------------------------------------
"""

from __future__ import annotations

import logging
import traceback
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from pathlib import Path
import sys
from datetime import datetime
import json
from typing import Any, Dict, Optional, Tuple
import threading

from click import get_current_context

# 延迟导入，避免循环导入
try:
    from app.core.config import settings
    from app.decorators.audit import get_current_request_id, get_current_user, get_request_context
except ImportError:
    # 开发环境中可能还未创建，提供默认值
    class Settings:
        DEBUG = False
        LOG_LEVEL = "INFO"
        LOG_DIR = "logs"


    settings = Settings()

    # 临时占位函数
    def get_current_request_id() -> Dict[str, Any]:
        return {"request_id": str(threading.current_thread().ident)}


    def get_current_user() -> Tuple[Optional[str], Optional[str]]:
        return (None, None)


class RequestContextFilter(logging.Filter):
    """
    请求上下文过滤器
    为日志记录添加请求上下文信息
    """

    def __init__(self, name: str = ""):
        super().__init__(name)
        self._context_cache = threading.local()

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            # 从装饰器获取请求ID
            ctx = get_current_request_id()
            context = get_request_context()

            record.request_id = getattr(record, 'request_id', ctx.get('request_id', None))

            # 添加请求信息
            record.method = getattr(record, 'method', context.get('method', None))
            record.path = getattr(record, 'path', context.get('path', None))


            # 获取用户信息
            user_info = get_current_user()
            if user_info and len(user_info) >= 2:
                record.user_id = user_info[0] or "anonymous"
                record.username = user_info[1] or "anonymous"
            else:
                record.user_id = "anonymous"
                record.username = "anonymous"

            # 添加时间戳
            record.timestamp = datetime.now().isoformat()

            # 添加进程和线程信息
            record.process_id = threading.get_ident()
            record.thread_name = threading.current_thread().name

            return True

        except Exception as e:
            # 如果获取上下文失败，设置默认值
            record.request_id = "--"
            record.user_id = "anonymous"
            record.username = "anonymous"
            record.error = f"Context filter error: {str(e)}"
            return True


class JsonFormatter(logging.Formatter):
    """
    JSON 格式日志
    自动附加请求上下文信息
    """

    def __init__(self, datefmt: str = None):
        super().__init__(datefmt=datefmt)
        self.datefmt = datefmt or "%Y-%m-%d %H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "process_id": getattr(record, 'process_id', None),
            "thread_name": getattr(record, 'thread_name', None),
        }

        # 添加请求上下文信息
        context_fields = ['request_id', 'user_id', 'username', 'path', 'method',
                          'client_host', 'client_port', 'endpoint', 'operation']

        for field in context_fields:
            value = getattr(record, field, None)
            if value is not None:
                log_record[field] = value

        # 异常堆栈
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
            log_record["traceback"] = traceback.format_exception(*record.exc_info)

        # 确保所有值都可序列化
        def make_serializable(obj):
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            elif isinstance(obj, (list, tuple)):
                return [make_serializable(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: make_serializable(value) for key, value in obj.items()}
            else:
                return str(obj)

        log_record = make_serializable(log_record)

        return json.dumps(log_record, ensure_ascii=False, separators=(',', ':'))


class FileFormatter(logging.Formatter):
    """
    控制台输出格式化器
    提供彩色输出和简洁格式
    """

    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',  # 青色
        'INFO': '\033[32m',  # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',  # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'  # 重置
    }

    def __init__(self, use_color: bool = True, datefmt: str = None):
        super().__init__(datefmt=datefmt)
        self.use_color = use_color
        self.datefmt = datefmt or "%Y-%m-%d %H:%M:%S.%f"[:-3]  # 毫秒精度

    def format(self, record: logging.LogRecord) -> str:
        # 时间戳
        time_str = datetime.fromtimestamp(record.created).strftime(self.datefmt)

        # 日志级别
        level = record.levelname

        # 请求上下文信息
        request_id = getattr(record, 'request_id', None)
        user_id = getattr(record, 'user_id', None)
        username = getattr(record, 'username', None)

        # 进程信息
        process_id = getattr(record, 'process_id', None)
        thread_name = getattr(record, 'thread_name', None)

        # 请求路径和方法（如果有）
        path = getattr(record, 'path', None)
        method = getattr(record, 'method', None)

        # 基础信息
        base_info = f"{time_str} | {level:8} | "

        # 添加上下文信息
        ctx_info = f"RID:{request_id}"

        if process_id and thread_name:
            ctx_info += f" | {thread_name} | PID:{process_id}"

        if user_id != "anonymous":
            ctx_info += f" | UID:{user_id}"

        if username != "anonymous":
            ctx_info += f" | {username}"

        if path and method:
            ctx_info += f" | {method} {path}"


        # 模块和行号
        location = f"{record.name}:{record.lineno}"

        # 消息
        message = record.getMessage()

        # 异常信息
        if record.exc_info:
            exc_info = "".join(traceback.format_exception(*record.exc_info))
            message = f"{message}\n{exc_info}"

        # 组合所有部分
        log_line = f"{base_info}{ctx_info} | {location} | {message}"

        return log_line


class ConsoleFormatter(logging.Formatter):
    """
    文件保存日志输格式化器
    """

    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',  # 青色
        'INFO': '\033[32m',  # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',  # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'  # 重置
    }

    def __init__(self, use_color: bool = True,datefmt: str = None):
        super().__init__(datefmt=datefmt)
        self.use_color = use_color
        self.datefmt = datefmt or "%Y-%m-%d %H:%M:%S.%f"[:-3]  # 毫秒精度

    def format(self, record: logging.LogRecord) -> str:
        # 时间戳
        time_str = datetime.fromtimestamp(record.created).strftime(self.datefmt)

        # 日志级别
        level = record.levelname

        # 颜色
        if self.use_color and level in self.COLORS:
            level_color = self.COLORS[level]
            reset_color = self.COLORS['RESET']
        else:
            level_color = ""
            reset_color = ""

        # 请求上下文信息
        request_id = getattr(record, 'request_id', None)
        user_id = getattr(record, 'user_id', None)
        username = getattr(record, 'username', None)

        # 进程信息
        process_id = getattr(record, 'process_id', None)
        thread_name = getattr(record, 'thread_name', None)

        # 请求路径和方法（如果有）
        path = getattr(record, 'path', None)
        method = getattr(record, 'method', None)

        # 基础信息
        base_info = f"{time_str} | {level_color}{level:8}{reset_color} | "

        # 添加上下文信息
        ctx_info = f"RID:{request_id}"

        if process_id and thread_name:
            ctx_info += f" | {thread_name} | PID:{process_id}"

        if user_id != "anonymous":
            ctx_info += f" | UID:{user_id}"

        if username != "anonymous":
            ctx_info += f" | {username}"

        if path and method:
            ctx_info += f" | {method} {path}"

        # 模块和行号
        location = f"{record.name}:{record.lineno}"

        # 消息
        message = record.getMessage()

        # 异常信息
        if record.exc_info:
            exc_info = "".join(traceback.format_exception(*record.exc_info))
            message = f"{message}\n{exc_info}"

        # 组合所有部分
        log_line = f"{base_info}{ctx_info} | {location} | {message}"

        return log_line


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """
    结构化日志适配器
    便于添加结构化字段
    """

    def process(self, msg: str, kwargs: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        extra = kwargs.get('extra', {})

        # 合并额外字段
        if self.extra:
            extra.update(self.extra)

        # 自动添加常用字段
        if 'endpoint' not in extra:
            extra['endpoint'] = f"{self.logger.name}.{kwargs.get('func', '--')}"

        if 'operation' not in extra:
            extra['operation'] = msg.split(' - ')[0] if ' - ' in msg else msg[:30]

        kwargs['extra'] = extra
        return msg, kwargs


def setup_logging(
        log_dir: Optional[str] = None,
        log_file: Optional[str] = None,
        log_level: Optional[str] = None,
        module_levels: Optional[Dict[str, str]] = None,
        use_json: bool = False,
        console_color: bool = True,
        max_bytes: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 10
) -> None:
    """
    初始化全局日志配置

    Args:
        log_dir: 日志目录
        log_file: 日志文件名
        log_level: 日志级别
        module_levels: 模块特定日志级别
        use_json: 是否使用JSON格式
        console_color: 控制台是否使用颜色
        max_bytes: 单个日志文件最大大小
        backup_count: 备份文件数量
    """
    # 获取当前文件的上级目录，逐级回溯到项目根目录（根据你的项目结构调整层级）
    # __file__ 是当前脚本文件路径，parent 逐级向上找根目录
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[2]
    # 强制指定根目录下的logs文件夹，覆盖传入的log_dir
    log_dir = project_root / "logs"

    # 获取配置
    log_dir = log_dir or getattr(settings, 'LOG_DIR', 'logs')
    log_level = log_level or getattr(settings, 'LOG_LEVEL', 'INFO')

    # 确保日志目录存在
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # 生成日志文件名
    if log_file is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = f"app_{date_str}.log"

    log_path = Path(log_dir) / log_file

    # 获取 root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # 清除现有的 handlers 和 filters
    root_logger.handlers.clear()
    root_logger.filters.clear()

    # 创建并添加过滤器
    context_filter = RequestContextFilter()
    root_logger.addFilter(context_filter)

    # 选择格式化器
    if use_json:
        formatter = JsonFormatter(datefmt="%Y-%m-%d %H:%M:%S.%f")
    else:
        formatter = ConsoleFormatter(
            use_color=console_color,
            datefmt="%Y-%m-%d %H:%M:%S.%f"
        )

    # 控制台 handler（始终启用）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    # 控制台使用彩色输出（如果可用且未禁用）
    if not use_json and console_color:
        console_formatter = ConsoleFormatter(
            use_color=True,
            datefmt="%Y-%m-%d %H:%M:%S.%f"
        )
        console_handler.setFormatter(console_formatter)
    else:
        console_handler.setFormatter(formatter)

    console_handler.addFilter(context_filter)
    root_logger.addHandler(console_handler)

    # 文件 handler（按大小轮转）
    file_handler = RotatingFileHandler(
        filename=str(log_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(
        FileFormatter()
    )
    file_handler.addFilter(context_filter)
    root_logger.addHandler(file_handler)

    # 错误日志文件 handler（单独记录ERROR及以上级别）
    error_log_path = Path(log_dir) / f"error_{datetime.now().strftime('%Y-%m-%d')}.log"
    error_handler = RotatingFileHandler(
        filename=str(error_log_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(context_filter)
    root_logger.addHandler(error_handler)

    # 应用模块特定的日志级别
    if module_levels:
        for module_name, module_level in module_levels.items():
            module_logger = logging.getLogger(module_name)
            module_logger.setLevel(getattr(logging, module_level.upper()))

    # 设置常见第三方库的日志级别
    third_party_loggers = {
        'uvicorn': 'WARNING',
        'uvicorn.access': 'WARNING',
        'fastapi': 'WARNING',
        'sqlalchemy': 'WARNING',
        'sqlalchemy.engine': 'WARNING',
        'aiosqlite': 'WARNING',
        'httpx': 'WARNING',
        'requests': 'WARNING',
    }

    for logger_name, level in third_party_loggers.items():
        logging.getLogger(logger_name).setLevel(getattr(logging, level))

    # 禁用不必要的传播
    root_logger.propagate = False

def get_logger(name: str = None, extra: Dict[str, Any] = None) -> StructuredLoggerAdapter:
    """
    获取结构化日志适配器

    Args:
        name: 日志器名称，默认使用调用模块名称
        extra: 额外字段

    Returns:
        StructuredLoggerAdapter实例
    """
    if name is None:
        # 获取调用模块的名称
        frame = sys._getframe(1)
        name = frame.f_globals.get('__name__', '--')

    logger = logging.getLogger(name)

    return StructuredLoggerAdapter(logger, extra or {})

