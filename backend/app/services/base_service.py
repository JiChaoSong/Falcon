#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-02 12:44
    Name  :     base_service
    Desc  :     
--------------------------------------
"""
import logging
import math
from datetime import datetime
from typing import TypeVar, Generic, Optional, Any, List, Type

from jinja2.nodes import Dict
from pydantic.v1.generics import GenericModel
from sqlalchemy import false
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from pydantic import BaseModel as PydanticBaseModel

from app.core.exception import ParamException
from app.decorators.audit import get_current_user
from app.models.base import BaseModel as SQLAlchemyBaseModel

ModelType = TypeVar('ModelType', bound=SQLAlchemyBaseModel)
CreateSchemaType = TypeVar('CreateSchemaType', bound=PydanticBaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=PydanticBaseModel)

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """基础服务类"""
    model_class: Type[ModelType]

    def __init__(self, db: Session, model_class):
        self.db = db
        self.model_class = model_class
        self.logger = logging.getLogger(__name__)

    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """创建记录"""
        pass

    def update(self, obj_in: UpdateSchemaType) -> ModelType:
        """更新记录"""
        pass

    def get(self, id: int) -> Optional[ModelType]:
        """根据ID获取记录"""
        pass

    def list(self, page: int = 1, page_size: int = 100, **kwargs):
        # 过滤 None 和空白字符串，保留 0、False 等合法值
        valid_query = {}
        for key, val in kwargs.items():
            if val is None:
                continue
            if isinstance(val, str) and not val.strip():
                continue
            valid_query[key] = val

        # 移除分页参数，避免作为查询条件传入filter
        valid_query.pop('page', None)
        valid_query.pop('page_size', None)

        page = max(page, 1)
        page_size = max(page_size, 1)
        offset_num = (page - 1) * page_size

        # SQLAlchemy 规范写法，使用 false() 替代 Python 布尔值
        query = self.db.query(self.model_class).filter(
            self.model_class.is_deleted  == false()
        )

        # 添加字符串模糊查询
        for field_name, value in valid_query.items():
            # 检查字段是否存在
            if not hasattr(self.model_class, field_name):
                continue

            field = getattr(self.model_class, field_name)

            # 只对字符串类型的字段使用模糊查询
            from sqlalchemy import String, Text

            if isinstance(field.type, (String, Text)):
                query = query.filter(field.ilike(f'%{value}%'))
            else:
                query = query.filter(field == value)

        # 总条数
        total = query.count()

        total_pages = math.ceil(total / page_size)  # 105 ÷ 10 = 10.5 → 向上取整 = 11

        # list数据
        model_class_list: List[ModelType] = query.order_by(
            self.model_class.created_at.desc()
        ).offset(offset_num).limit(page_size).all()

        # 排序 + 分页 + 查询
        return {
            'results': model_class_list,
            'total': total,
            'total_pages': total_pages,
            'page': page,
            'page_size': page_size,
        }

    def delete(self, id: int) -> Optional[bool]:
        pass

    def _commit(self, entity, success_msg, fail_msg, operation=None, extra=None):
        try:
            self.db.commit()
            self.db.refresh(entity)

            log_extra = {"operation": operation} if operation else {}
            if extra:
                log_extra.update(extra)

            self.logger.info(success_msg, extra=log_extra)

            return entity

        except SQLAlchemyError as e:
            self.db.rollback()

            self.logger.error(
                f"{fail_msg} - 数据库错误: {str(e)}",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    **(extra or {})
                }
            )
            raise ParamException(f"{fail_msg}: {str(e)}")
