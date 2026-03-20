#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-03-20 10:28 
    Name  :     banner.py
    Desc  :     
--------------------------------------
"""
from __future__ import annotations

from pyfiglet import Figlet
from app.settings import worker_settings
from app.logging_config import get_worker_logger

logger = get_worker_logger(__name__, worker_id=worker_settings.GRPC_WORKER_ID)


def print_color_banner():
    # 自动生成艺术字
    f = Figlet(font='slant')
    banner_text = f.renderText(f'{worker_settings.PROJECT_NAME}')

    banner_str = f"""
┌────────────────────────────────────────────────┐
{banner_text}
Falcon Worker Service
Version: {worker_settings.VERSION}
Worker Port: {worker_settings.GRPC_WORKER_PORT} | gRPC Server: {worker_settings.GRPC_MASTER_PORT}
└────────────────────────────────────────────────┘    
"""

    logger.info(banner_str)

