#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-05 10:21 
    Name  :     case_service.py
    Desc  :     
--------------------------------------
"""

from typing import Optional, Dict, Any

from sqlalchemy import Select, false
from sqlalchemy.exc import SQLAlchemyError

from app.core.exception import ParamException
from app.models import Case
from app.schemas import case as schemas
from app.services.base_service import BaseService, ModelType
from sqlalchemy.orm import Session

import logging


class CaseService(BaseService[Case, schemas.CaseCreate, schemas.CaseUpdate]):

    def __init__(self, db: Session):
        super().__init__(db, Case)
        self.logger = logging.getLogger(__name__)


    def _get_case_by_id(self, case_id: int) -> Case:
        """根据用例id获取用例"""
        case = self.db.execute(
            Select(Case).where(
                Case.id == case_id,
                Case.is_deleted == false()
            )
        ).scalar_one_or_none()

        if not case:
            self.logger.error(f'用例不存在:{case_id}')
            raise ParamException('用例不存在')

        return case

    def _validate_case_name_unique(self, name: str, exclude_case_id: int = None) -> None:
        query = Select(Case).where(
            Case.name == name,
            Case.is_deleted == false()
        )
        if exclude_case_id:
            query = query.where(Case.id == exclude_case_id)

        existing_case = self.db.execute(query).scalar_one_or_none()

        if  existing_case:
            raise ParamException('用例名称已存在')

    def get(self, id: int) -> Optional[ModelType]:

        return self._get_case_by_id(id)

    def delete(self, id: int) -> Optional[bool]:

        case = self._get_case_by_id(id)

        if getattr(case, 'is_deleted', False):
            self.logger.warning(
                f"用例已被删除 - ID: {id}",
                extra={
                    "operation": "case_delete",
                    "error": "用例已被删除"
                }
            )
            raise ParamException("用例已被删除")

        # 检查模型是否支持软删除
        if not hasattr(case, 'is_deleted'):
            self.logger.warning(
                f"模型不支持软删除 - 模型: {self.model_class.__name__}, ID: {id}",
                extra={
                    "model": f'{self.model_class.__name__}',
                    "operation": "case_delete",
                    "error": "模型不支持软删除"
                }
            )
            raise ParamException(f"{self.model_class.__name__}不支持删除")


        case.soft_delete()

        # 保存到数据库
        self._commit(
            case,
            success_msg=f"用例删除成功 - ID: {id}, 用例名称: {case.name}",
            fail_msg="用例删除失败",
            operation="case_delete",
            extra=None
        )

        return True

    def create(self, data: schemas.CaseCreate) -> Dict[str, Any] | None:

        create_data = data.model_dump()

        name = create_data.get('name')

        self._validate_case_name_unique(name)

        new_case = Case(**create_data)

        self.db.add(new_case)

        self._commit(
            new_case,
            success_msg=f"用例创建成功 - 用例名称: {name}",
            fail_msg=f"用例{name}创建失败",
            operation="case_create"
        )

        return new_case.to_dict()

    def update(self, data: schemas.CaseUpdate) -> Dict[str, Any] | None:

        update_data = data.model_dump()

        name = update_data.get('name')
        case_id = update_data.get('id')

        case = self._get_case_by_id(case_id)

        self._validate_case_name_unique(name, case_id)

        for field, value in update_data.items():
            # 跳过不允许直接更新的字段
            if field in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by'
                         , 'is_deleted', 'created_by_name', 'updated_by_name', 'deleted_by_name']:
                continue

            if hasattr(case, field) and getattr(case, field) != value:
                setattr(case, field, value)

        self._commit(
            case,
            success_msg=f"用例更新成功 - ID: {case_id}, 用例名称: {name}",
            fail_msg="用例更新失败",
            operation="case_update",
            extra={"updated_fields": list(update_data.keys())}
        )

        return case.to_dict()

    def config(self, data: schemas.CaseConfig) -> Dict[str, Any] | None:
        """用例配置"""

        config_data = data.model_dump()

        case_id = config_data.get('id')

        case = self._get_case_by_id(case_id)

        for field, value in config_data.items():
            # 跳过不允许直接更新的字段
            if field in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by'
                         , 'is_deleted', 'created_by_name', 'updated_by_name', 'deleted_by_name']:
                continue

            if hasattr(case, field) and getattr(case, field) != value:
                setattr(case, field, value)

        self._commit(
            case,
            success_msg=f"用例更新成功 - ID: {case_id}, 用例名称: {case.name}",
            fail_msg="用例更新失败",
            operation="case_config",
            extra={"updated_fields": list(config_data.keys())}
        )

        return case.to_dict()
