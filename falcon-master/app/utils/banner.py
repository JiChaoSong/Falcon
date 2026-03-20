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
from app.core.config import settings
from app.core.logging_config import get_logger
from app.utils.time_utils import beijing_now_string

logger = get_logger(__name__)

def print_color_banner():
    # 自动生成艺术字
    f = Figlet(font='slant')
    banner_text = f.renderText(f'{settings.PROJECT_NAME}')

    banner_str =f"""
┌────────────────────────────────────────────────┐
{banner_text}
Falcon Master Service
Version: {settings.VERSION}
Port: {settings.PORT} | gRPC: {settings.GRPC_MASTER_PORT}
Start Time {beijing_now_string()}
└────────────────────────────────────────────────┘    
"""

    logger.info(banner_str)

