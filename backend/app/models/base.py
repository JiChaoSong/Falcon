#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-02 12:20
    Name  :     base
    Desc  :     
--------------------------------------
"""
from datetime import datetime
from typing import Optional, Dict, Any

import inflection
from sqlalchemy import BigInteger, Boolean, DateTime, func, inspect, String
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, declared_attr

from app.db import Base
from app.decorators.audit import get_current_user
from app.utils.id_generator import generate_id
from app.utils.time_utils import utc_now


class BaseModel(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
        default=generate_id,
        index=True,
        comment="主键ID"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )

    created_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="创建人ID"
    )

    created_by_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="创建人"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )

    updated_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="更新人ID"
    )

    updated_by_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="更新人"
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已删除"
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="删除时间"
    )

    deleted_by: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="删除人ID"
    )

    deleted_by_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="删除人"
    )

    @declared_attr
    def __tablename__(cls) -> str:
        """自动生成表名（复数形式）"""
        return inflection.pluralize(inflection.underscore(cls.__name__))

    def to_dict(self, exclude: Optional[list] = None) -> Dict[str, Any]:
        if exclude is None:
            exclude = []

        result = {}

        for column in inspect(self.__class__).columns:
            key = column.key

            if key in exclude:
                continue

            value = getattr(self, key)

            if isinstance(value, datetime):
                value = value.isoformat()

            result[key] = value

        return result

    def update(self, **kwargs):
        """更新模型字段"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def soft_delete(self):
        """软删除"""
        uid, uname = get_current_user()

        self.is_deleted = True
        self.deleted_at = utc_now()

        if hasattr(self, "deleted_by"):
            self.deleted_by = uid

        if hasattr(self, "deleted_by_name"):
            self.deleted_by_name = uname

    def restore(self, restored_by: Optional[int] = None):
        """恢复删除"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.deleted_by_name = None

    def __repr__(self) -> str:
        """友好的字符串表示"""
        return f"<{self.__class__.__name__}(id={self.id})>"
