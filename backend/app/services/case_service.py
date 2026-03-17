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

from enum import Enum
from typing import Optional, Dict, Any

from sqlalchemy import Select, false, String, Text, cast, func, or_
from sqlalchemy.exc import SQLAlchemyError

from app.core.exception import ParamException
from app.models import Case
from app.schemas import case as schemas
from app.services.access_control_service import AccessControlService
from app.services.base_service import BaseService, ModelType
from sqlalchemy.orm import Session

import logging


class CaseService(BaseService[Case, schemas.CaseCreate, schemas.CaseUpdate]):

    def __init__(self, db: Session):
        super().__init__(db, Case)
        self.logger = logging.getLogger(__name__)
        self.access_control = AccessControlService(db)


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

        self.access_control.ensure_project_view_access(case.project_id)
        return case

    def _validate_case_name_unique(self, name: str, exclude_case_id: int = None) -> None:
        if not name:
            return

        query = Select(Case).where(
            Case.name == name,
            Case.is_deleted == false()
        )
        if exclude_case_id:
            query = query.where(Case.id != exclude_case_id)

        existing_case = self.db.execute(query).scalar_one_or_none()

        if  existing_case:
            raise ParamException('用例名称已存在')

    def get(self, id: int) -> Optional[ModelType]:

        return self._get_case_by_id(id)

    def delete(self, id: int) -> Optional[bool]:

        case = self._get_case_by_id(id)
        self.access_control.ensure_project_manage_access(case.project_id)

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
        self.access_control.ensure_project_manage_access(create_data.get('project_id'))

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
        # 只更新显式传入的字段，避免批量启停这类请求把其他可选字段覆盖为 None
        update_data = data.model_dump(exclude_unset=True)

        name = update_data.get('name')
        case_id = update_data.get('id')

        case = self._get_case_by_id(case_id)
        self.access_control.ensure_project_manage_access(case.project_id)

        target_project_id = update_data.get('project_id')
        if target_project_id is not None and target_project_id != case.project_id:
            self.access_control.ensure_project_manage_access(target_project_id)

        if name and name != case.name:
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

        config_data = data.model_dump(exclude_unset=True)

        case_id = config_data.get('id')

        case = self._get_case_by_id(case_id)
        self.access_control.ensure_project_manage_access(case.project_id)

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

    def list(self, page: int = 1, page_size: int = 10, **kwargs):
        accessible_project_ids = self.access_control.get_accessible_project_ids()
        if accessible_project_ids is not None:
            if not accessible_project_ids:
                return {
                    'results': [],
                    'total': 0,
                    'total_pages': 0,
                    'page': page,
                    'page_size': page_size,
                }

            project_id = kwargs.get("project_id")
            if project_id is not None and project_id not in accessible_project_ids:
                return {
                    'results': [],
                    'total': 0,
                    'total_pages': 0,
                    'page': page,
                    'page_size': page_size,
                }

            query = self.db.query(self.model_class).filter(
                self.model_class.is_deleted == false(),
                self.model_class.project_id.in_(accessible_project_ids),
            )

            valid_query = {
                key: val for key, val in kwargs.items()
                if val is not None and not (isinstance(val, str) and not val.strip())
            }
            valid_query.pop('page', None)
            valid_query.pop('page_size', None)
            for field_name, value in valid_query.items():
                if not hasattr(self.model_class, field_name):
                    continue
                field = getattr(self.model_class, field_name)
                if isinstance(value, Enum):
                    enum_candidates = {
                        value.value,
                        value.name,
                        str(value.value).lower(),
                        str(value.name).lower(),
                        str(value.value).upper(),
                        str(value.name).upper(),
                    }
                    query = query.filter(
                        or_(*[
                            func.lower(cast(field, String)) == str(candidate).lower()
                            for candidate in enum_candidates
                        ])
                    )
                elif isinstance(field.type, (String, Text)):
                    query = query.filter(field.ilike(f'%{value}%'))
                else:
                    query = query.filter(field == value)

            total = query.count()
            total_pages = (total + page_size - 1) // page_size if total else 0
            offset_num = (page - 1) * page_size
            results = query.order_by(self.model_class.created_at.desc()).offset(offset_num).limit(page_size).all()
            return {
                'results': results,
                'total': total,
                'total_pages': total_pages,
                'page': page,
                'page_size': page_size,
            }

        return super().list(page=page, page_size=page_size, **kwargs)
