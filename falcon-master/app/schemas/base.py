#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-05 9:00 
    Name  :     base.py
    Desc  :     
--------------------------------------
"""
from datetime import datetime
from typing import List

from pydantic import BaseModel


class BaseSchema(BaseModel):
    id: int
    created_at: datetime | None
    created_by: int | None
    created_by_name: str | None
    updated_at: datetime | None
    updated_by: int | None
    updated_by_name: str | None
    is_deleted: bool

class BaseListSchema(BaseModel):

    page: int
    page_size: int
    total_pages: int
    total: int
    results: List


class BaseQuery(BaseModel):
    page: int
    page_size: int