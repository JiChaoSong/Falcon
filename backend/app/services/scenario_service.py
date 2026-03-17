#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-05 11:13 
    Name  :     scenario_service.py
    Desc  :     
--------------------------------------
"""
from typing import Optional, Dict, Any, List

from sqlalchemy import Select, false, Delete
from sqlalchemy.exc import SQLAlchemyError

from app.core.exception import ParamException
from app.models import Scenario, ScenarioCase
from app.schemas import scenario as schemas
from app.services.base_service import BaseService, ModelType
from sqlalchemy.orm import Session

import logging


class ScenarioService(BaseService[Scenario, schemas.ScenarioCreate, schemas.ScenarioUpdate]):

    def __init__(self, db: Session):
        super().__init__(db, Scenario)
        self.logger = logging.getLogger(__name__)


    def _get_scenario_by_id(self, scenario_id: int) -> Optional[Scenario]:
        """根据场景id获取场景"""
        scenario = self.db.execute(
            Select(Scenario).where(
                Scenario.id == scenario_id,
                Scenario.is_deleted == false()
            )
        ).scalar_one_or_none()

        if not scenario:
            self.logger.error(f'场景不存在:{scenario_id}')
            raise ParamException('场景不存在')

        return scenario

    def _validate_scenario_name_unique(self, name: str,
                                       exclude_scenario_id: int = None,
                                       project_id: int = None) -> None:
        """验证场景名称在项目内唯一"""
        query = Select(Scenario).where(
            Scenario.name == name,
            Scenario.is_deleted == false()
        )

        if project_id:
            query = query.where(Scenario.project_id == project_id)

        if exclude_scenario_id:
            query = query.where(Scenario.id != exclude_scenario_id)

        existing_scenario = self.db.execute(query).scalar_one_or_none()

        if existing_scenario:
            raise ParamException('场景名称已存在')

    def _update_scenario_cases(self, scenario_id: int, cases: List[schemas.ScenarioCaseBind]) -> None:
        """
        更新场景的用例关联
        先删除所有现有关联，再重新创建
        """
        try:
            # 1. 删除现有关联
            self.db.execute(
                Delete(ScenarioCase).where(ScenarioCase.scenario_id == scenario_id)
            )

            # 2. 创建新的关联
            if cases:
                for case_bind in cases:
                    scenario_case = ScenarioCase(
                        scenario_id=scenario_id,
                        case_id=case_bind.case_id,
                        order=case_bind.order,
                        weight=case_bind.weight
                    )
                    self.db.add(scenario_case)

                # 3. 更新场景的用例总数
                total_cases = len(cases)
                self.db.execute(
                    Select(Scenario).where(Scenario.id == scenario_id)
                ).scalar_one().total_testcases = total_cases
            else:
                # 如果没有用例，将总数设为0
                self.db.execute(
                    Select(Scenario).where(Scenario.id == scenario_id)
                ).scalar_one().total_testcases = 0

        except SQLAlchemyError as e:
            self.logger.error(f"更新场景用例关联失败: {str(e)}")
            raise ParamException("更新场景用例关联失败")

    def get(self, id: int) -> Dict[str, Any] | None:
        """获取场景详情（包含关联的用例）"""
        # 获取场景基本信息
        scenario = self._get_scenario_by_id(id)

        # 获取关联的用例列表
        case_query = Select(ScenarioCase).where(
            ScenarioCase.scenario_id == id
        ).order_by(ScenarioCase.order)

        scenario_cases = self.db.execute(case_query).scalars().all()

        # 转换为字典并添加用例信息
        result = scenario.to_dict()
        result['cases'] = [
            {
                'case_id': sc.case_id,
                'order': sc.order,
                'weight': sc.weight
            }
            for sc in scenario_cases
        ]

        return result

    def delete(self, id: int) -> Optional[bool]:
        """删除场景（软删除）"""
        scenario = self._get_scenario_by_id(id)

        if getattr(scenario, 'is_deleted', False):
            self.logger.warning(f"场景已被删除 - ID: {id}")
            raise ParamException("场景已被删除")

        if not hasattr(scenario, 'is_deleted'):
            self.logger.warning(f"模型不支持软删除 - 模型: {self.model_class.__name__}")
            raise ParamException(f"{self.model_class.__name__}不支持删除")

        # 执行软删除
        scenario.soft_delete()

        # 同时删除关联的用例关系（可选，根据业务需求决定是否保留关联关系）
        try:
            self.db.execute(
                Delete(ScenarioCase).where(ScenarioCase.scenario_id == id)
            )
        except SQLAlchemyError as e:
            self.logger.warning(f"删除场景用例关联失败: {str(e)}")

        self._commit(
            scenario,
            success_msg=f"场景删除成功 - ID: {id}, 场景名称: {scenario.name}",
            fail_msg="场景删除失败",
            operation="scenario_delete"
        )

        return True
    def create(self, data: schemas.ScenarioCreate) -> Dict[str, Any] | None:

        create_data = data.model_dump()

        name = create_data.get('name')
        project_id = create_data.get('project_id')

        cases = create_data.pop('cases', [])  # 提取cases，从主数据中移除

        self._validate_scenario_name_unique(name=name, project_id = project_id)

        new_scenario = Scenario(**create_data)

        self.db.add(new_scenario)

        # 刷新以获取自增ID
        self.db.flush()

        try:
            # 创建用例关联
            if cases:
                for case_bind in cases:
                    scenario_case = ScenarioCase(
                        scenario_id=new_scenario.id,
                        case_id=case_bind.case_id,
                        order=case_bind.order,
                        weight=case_bind.weight
                    )
                    self.db.add(scenario_case)
            self._commit(
                new_scenario,
                success_msg=f"场景创建成功 - 场景名称: {name}",
                fail_msg=f"场景{name}创建失败",
                operation="case_create"
            )

            # 返回包含用例信息的结果
            result = new_scenario.to_dict()
            result['cases'] = [
                {
                    'case_id': cb.case_id,
                    'order': cb.order,
                    'weight': cb.weight
                }
                for cb in cases
            ]

            return result

        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"创建场景失败: {str(e)}")
            raise ParamException("创建场景失败")

    def update(self, data: schemas.ScenarioUpdate) -> Dict[str, Any] | None:
        """更新场景（包含关联用例）"""

        update_data = data.model_dump(exclude_unset=True)  # 只包含实际传入的字段
        scenario_id = update_data.get('id')
        cases = update_data.pop('cases', None)  # 提取cases，None表示不更新

        if not scenario_id:
            raise ParamException("场景ID不能为空")

        # 获取现有场景
        scenario = self._get_scenario_by_id(scenario_id)

        # 验证名称唯一性（如果名称有更新）
        if 'name' in update_data:
            name = update_data['name']
            project_id = update_data.get('project_id', scenario.project_id)
            self._validate_scenario_name_unique(
                name,
                exclude_scenario_id=scenario_id,
                project_id=project_id
            )

        # 更新场景基本信息
        for field, value in update_data.items():
            if field in ['id', 'created_at', 'updated_at', 'created_by',
                         'updated_by', 'is_deleted', 'created_by_name',
                         'updated_by_name', 'deleted_by_name']:
                continue

            if hasattr(scenario, field) and getattr(scenario, field) != value:
                setattr(scenario, field, value)

        # 更新关联用例（如果提供了cases）
        if cases is not None:
            self._update_scenario_cases(scenario_id, cases)

        self._commit(
            scenario,
            success_msg=f"场景更新成功 - ID: {scenario_id}, 场景名称: {scenario.name}",
            fail_msg="场景更新失败",
            operation="scenario_update",
            extra={"updated_fields": list(update_data.keys())}
        )

        # 返回更新后的结果
        result = scenario.to_dict()
        if cases is not None:
            result['cases'] = [
                {
                    'case_id': cb.case_id,
                    'order': cb.order,
                    'weight': cb.weight
                }
                for cb in cases
            ]

        return result
