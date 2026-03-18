#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-03 11:44 
    Name  :     audit.py
    Desc  :     
--------------------------------------
"""
from sqlalchemy import event, inspect
from sqlalchemy.orm import Mapper, Session
from app.decorators.audit import get_current_user
from app.utils.time_utils import utc_now

import logging
logger = logging.getLogger(__name__)

def register_audit_listeners(base):
    """
    注册审计字段自动填充
    """
    # ===== 插入前 =====
    @event.listens_for(base, "before_insert", propagate=True)
    def before_insert(mapper: Mapper, connection, target):
        uid, uname = get_current_user()
        current_time = utc_now()

        # 设置时间字段
        if hasattr(target, "created_at"):
            target.created_at = current_time

        if hasattr(target, "updated_at"):
            target.updated_at = current_time

        # 设置用户字段
        if uid:
            if hasattr(target, "created_by"):
                target.created_by = uid

            if hasattr(target, "updated_by"):
                target.updated_by = uid

        if uname:
            if hasattr(target, "created_by_name"):
                target.created_by_name = uname

            if hasattr(target, "updated_by_name"):
                target.updated_by_name = uname

    @event.listens_for(base, "before_update", propagate=True)
    def before_update(mapper, connection, target):
        uid, uname = get_current_user()
        current_time = utc_now()

        def has_attr(name):
            return hasattr(target, name)

        # 更新时间
        if has_attr("updated_at"):
            target.updated_at = current_time

        # 判断软删除
        is_deleting = False

        if has_attr("is_deleted"):
            insp = inspect(target)
            state = insp.attrs.is_deleted

            try:
                if state.history.has_changes():
                    added = state.history.added
                    if added and added[0] is True:
                        is_deleting = True
                else:
                    if bool(getattr(target, "is_deleted", False)):
                        is_deleting = True
            except Exception as e:
                logger.warning(f"审计判断异常: {e}")

        # 软删除字段
        if is_deleting:
            if has_attr("deleted_at"):
                target.deleted_at = current_time

            if uid is not None and has_attr("deleted_by"):
                target.deleted_by = uid

            if uname and has_attr("deleted_by_name"):
                target.deleted_by_name = uname

        # 更新人
        if uid is not None and has_attr("updated_by"):
            target.updated_by = uid

        if uname and has_attr("updated_by_name"):
            target.updated_by_name = uname
