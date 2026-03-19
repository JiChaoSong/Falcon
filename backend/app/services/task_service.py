#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-05 11:13
    Name  :     task_service.py
    Desc  :     任务服务
--------------------------------------
"""
import math
from contextlib import contextmanager
from enum import Enum
from typing import Optional, Dict, Any, List

import logging
import time
from sqlalchemy import Select, false, select, Delete, cast, func, or_, exists
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import String, Text

from app.core.exception import ParamException
from app.models import Tasks, TaskScenario, Scenario, ScenarioCase, Case, TaskExecutionStrategyEnum
from app.schemas import task as schemas
from app.services.access_control_service import AccessControlService
from app.services.base_service import BaseService, ModelType



class TaskService(BaseService[Tasks, schemas.TaskCreate, schemas.TaskUpdate]):
    def __init__(self, db: Session):
        super().__init__(db, Tasks)
        # 可以重写基类的logger，使日志显示正确的服务名称
        self.logger = logging.getLogger(__name__)
        self.access_control = AccessControlService(db)

    @contextmanager
    def _transaction_with_retry(self, max_retries: int = 3):
        """带有重试机制的事务上下文管理器"""
        for attempt in range(max_retries):
            try:
                yield
                self.db.commit()
                break
            except IntegrityError as e:
                self.db.rollback()
                if "uq_task_project_name" in str(e):
                    if attempt == max_retries - 1:
                        raise ParamException("任务名称已存在，请重试")
                elif "deadlock" in str(e).lower():
                    if attempt == max_retries - 1:
                        raise ParamException("系统繁忙，请稍后重试")
                    time.sleep(0.1 * (2 ** attempt))
                else:
                    raise
            except Exception as e:
                self.db.rollback()
                raise

    def _get_task_by_id(self, task_id: int) -> Tasks:
        """根据任务id获取任务"""
        task = self.db.execute(
            Select(Tasks).where(
                Tasks.id == task_id,
                Tasks.is_deleted == false()
            )
        ).scalar_one_or_none()

        if not task:
            self.logger.error(f'任务不存在:{task_id}')
            raise ParamException('任务不存在')
        self.access_control.ensure_project_view_access(task.project_id)
        return task

    def _validate_task_name_unique(self, name: str, project_id: int,
                                   exclude_task_id: int = None) -> None:
        """验证同一项目下任务名称唯一性"""
        query = select(Tasks).where(
            Tasks.name == name,
            Tasks.project_id == project_id,
            Tasks.is_deleted == false()
        )

        if exclude_task_id:
            query = query.where(Tasks.id != exclude_task_id)

        existing_task = self.db.execute(query).scalar_one_or_none()

        if existing_task:
            raise ParamException('任务名称已存在')

    def _get_valid_scenarios(
        self,
        project_id: int,
        scenario_binds: List[schemas.TaskScenarioBind],
    ) -> list[Scenario]:
        if not scenario_binds:
            raise ParamException("任务至少需要关联一个场景")

        scenario_ids = [item.scenario_id for item in scenario_binds]
        if len(scenario_ids) != len(set(scenario_ids)):
            raise ParamException("任务中存在重复场景")

        scenarios = self.db.execute(
            Select(Scenario).where(
                Scenario.id.in_(scenario_ids),
                Scenario.project_id == project_id,
                Scenario.is_deleted == false(),
            )
        ).scalars().all()

        scenario_map = {scenario.id: scenario for scenario in scenarios}
        missing_ids = [scenario_id for scenario_id in scenario_ids if scenario_id not in scenario_map]
        if missing_ids:
            raise ParamException(f"场景不存在或不属于当前项目: {missing_ids}")

        return [scenario_map[item.scenario_id] for item in scenario_binds]

    def _validate_task_strategy_config(
        self,
        execution_strategy: TaskExecutionStrategyEnum | None,
        scenario_binds: List[schemas.TaskScenarioBind],
    ) -> None:
        if execution_strategy != TaskExecutionStrategyEnum.WEIGHTED:
            return

        total_weight = sum(max(int(item.weight or 0), 0) for item in scenario_binds)
        if total_weight <= 0:
            raise ParamException("按权重分配时，场景权重总和必须大于 0")

    def _replace_task_scenarios(
        self,
        task_id: int,
        project_id: int,
        scenario_binds: List[schemas.TaskScenarioBind],
    ) -> None:
        scenarios = self._get_valid_scenarios(project_id, scenario_binds)

        self.db.execute(
            Delete(TaskScenario).where(TaskScenario.task_id == task_id)
        )

        for bind, scenario in zip(scenario_binds, scenarios):
            self.db.add(
                TaskScenario(
                    task_id=task_id,
                    scenario_id=scenario.id,
                    scenario=scenario.name,
                    order=bind.order,
                    weight=bind.weight,
                    target_users=bind.target_users,
                )
            )

    def _load_scenario_cases(self, scenario_id: int) -> list[dict[str, Any]]:
        scenario_cases = self.db.execute(
            Select(ScenarioCase).where(
                ScenarioCase.scenario_id == scenario_id,
                ScenarioCase.is_deleted == false(),
            ).order_by(ScenarioCase.order.asc(), ScenarioCase.id.asc())
        ).scalars().all()

        case_ids = [item.case_id for item in scenario_cases]
        if not case_ids:
            return []

        cases = self.db.execute(
            Select(Case).where(
                Case.id.in_(case_ids),
                Case.is_deleted == false(),
            )
        ).scalars().all()
        case_map = {item.id: item for item in cases}

        results: list[dict[str, Any]] = []
        for scenario_case in scenario_cases:
            case = case_map.get(scenario_case.case_id)
            if not case:
                continue
            results.append(
                {
                    "id": case.id,
                    "name": case.name,
                    "method": case.method,
                    "url": case.url,
                    "status": getattr(case.status, "value", str(case.status)),
                    "order": scenario_case.order,
                    "weight": scenario_case.weight,
                }
            )
        return results

    def _load_task_scenarios(self, task_id: int) -> list[dict[str, Any]]:
        task_scenarios = self.db.execute(
            Select(TaskScenario).where(
                TaskScenario.task_id == task_id,
                TaskScenario.is_deleted == false(),
            ).order_by(TaskScenario.order.asc(), TaskScenario.id.asc())
        ).scalars().all()

        return [
            {
                "scenario_id": item.scenario_id,
                "scenario": item.scenario,
                "order": item.order,
                "weight": item.weight,
                "target_users": item.target_users,
                "cases": self._load_scenario_cases(item.scenario_id),
            }
            for item in task_scenarios
        ]

    def _serialize_task(self, task: Tasks) -> Dict[str, Any]:
        task_data = task.to_dict()
        task_data["scenarios"] = self._load_task_scenarios(task.id)
        return task_data

    def get(self, id: int) -> Optional[ModelType]:
        task = self._get_task_by_id(id)
        return self._serialize_task(task)

    def list(self, page: int = 1, page_size: int = 10, **kwargs):
        scenario_id = kwargs.pop("scenario_id", None)
        query = self.db.query(Tasks).filter(Tasks.is_deleted == false())
        accessible_project_ids = self.access_control.get_accessible_project_ids()

        if accessible_project_ids is not None:
            if not accessible_project_ids:
                return {
                    "results": [],
                    "total": 0,
                    "total_pages": 0,
                    "page": page,
                    "page_size": page_size,
                }
            query = query.filter(Tasks.project_id.in_(accessible_project_ids))

        if scenario_id is not None:
            query = query.filter(
                exists(
                    Select(TaskScenario.task_id).where(
                        TaskScenario.task_id == Tasks.id,
                        TaskScenario.scenario_id == scenario_id,
                        TaskScenario.is_deleted == false(),
                    )
                )
            )

        valid_query = {
            key: val for key, val in kwargs.items()
            if val is not None and not (isinstance(val, str) and not val.strip())
        }
        valid_query.pop("page", None)
        valid_query.pop("page_size", None)

        for field_name, value in valid_query.items():
            if not hasattr(Tasks, field_name):
                continue

            field = getattr(Tasks, field_name)
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
                query = query.filter(field.ilike(f"%{value}%"))
            else:
                query = query.filter(field == value)

        total = query.count()
        total_pages = math.ceil(total / page_size) if total else 0
        offset_num = (page - 1) * page_size

        task_list = query.order_by(
            Tasks.created_at.desc()
        ).offset(offset_num).limit(page_size).all()

        return {
            "results": [self._serialize_task(task) for task in task_list],
            "total": total,
            "total_pages": total_pages,
            "page": page,
            "page_size": page_size,
        }

    def delete(self, id: int) -> bool:
        """删除任务（软删除）"""
        with self._transaction_with_retry():
            task = self._get_task_by_id(id)
            self.access_control.ensure_project_manage_access(task.project_id)

            if getattr(task, 'is_deleted', False):
                self.logger.warning(f"任务已被删除 - ID: {id}")
                raise ParamException("任务已被删除")

            if not hasattr(task, 'is_deleted'):
                self.logger.warning(f"模型不支持软删除 - 模型: {self.model_class.__name__}")
                raise ParamException(f"{self.model_class.__name__}不支持删除")

            task.soft_delete()
            task_scenarios = self.db.execute(
                Select(TaskScenario).where(
                    TaskScenario.task_id == id,
                    TaskScenario.is_deleted == false(),
                )
            ).scalars().all()
            for task_scenario in task_scenarios:
                task_scenario.soft_delete()

            # 使用基类的_commit方法进行日志记录和提交（替换原本的直接提交）
            self._commit(
                task,
                success_msg=f"任务删除成功 - ID: {id}, 任务名称: {task.name}",
                fail_msg="任务删除失败",
                operation="task_delete"
            )

            return True

    def create(self, data: schemas.TaskCreate) -> Dict[str, Any]:
        """创建任务（线程安全）"""
        create_data = data.model_dump()
        name = create_data.get('name')
        project_id = create_data.get('project_id')
        self.access_control.ensure_project_manage_access(project_id)
        scenarios = [schemas.TaskScenarioBind(**item) for item in create_data.pop("scenarios", [])]
        execution_strategy = create_data.get("execution_strategy")
        self._validate_task_strategy_config(execution_strategy, scenarios)

        try:
            # 验证名称唯一性
            self._validate_task_name_unique(name, project_id)

            # 创建任务
            new_task = Tasks(**create_data)
            self.db.add(new_task)
            self.db.flush()
            self._replace_task_scenarios(new_task.id, project_id, scenarios)

            # 使用基类的_commit方法
            self._commit(
                new_task,
                success_msg=f"任务创建成功 - 任务名称: {name}",
                fail_msg=f"任务{name}创建失败",
                operation="task_create"
            )

            return self._serialize_task(new_task)

        except IntegrityError as e:
            if "uq_task_project_name" in str(e):
                raise ParamException(f"项目下已存在同名任务: {name}")
            raise

    def update(self, data: schemas.TaskUpdate) -> Dict[str, Any]:
        """更新任务"""
        update_data = data.model_dump(exclude_unset=True)
        task_id = update_data.get('id')
        name = update_data.get('name')
        project_id = update_data.get('project_id')
        scenarios = update_data.pop("scenarios", None)
        execution_strategy = update_data.get("execution_strategy")

        if not task_id:
            raise ParamException("任务ID不能为空")

        try:
            # 获取任务
            task = self._get_task_by_id(task_id)
            self.access_control.ensure_project_manage_access(task.project_id)

            if project_id is not None and project_id != task.project_id and scenarios is None:
                raise ParamException("修改所属项目时，请同时更新场景列表")

            # 如果名称有更新，验证唯一性
            if name is not None or project_id is not None:
                check_name = name if name is not None else task.name
                check_project_id = project_id if project_id is not None else task.project_id

                if check_name != task.name or check_project_id != task.project_id:
                    self._validate_task_name_unique(check_name, check_project_id, task_id)

            # 更新字段
            updated_fields = []
            for field, value in update_data.items():
                if field in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by',
                             'is_deleted', 'created_by_name', 'updated_by_name', 'deleted_by_name']:
                    continue

                if hasattr(task, field):
                    column = task.__table__.columns.get(field)
                    if column is not None:
                        if not column.nullable and value is None:
                            continue

                        current_value = getattr(task, field)
                        if current_value != value:
                            setattr(task, field, value)
                            updated_fields.append(field)

            if scenarios is not None:
                scenario_binds = [schemas.TaskScenarioBind(**item) for item in scenarios]
                self._validate_task_strategy_config(execution_strategy or task.execution_strategy, scenario_binds)
                current_project_id = task.project_id
                self._replace_task_scenarios(task.id, current_project_id, scenario_binds)
                updated_fields.append("scenarios")

            if updated_fields:
                # 使用基类的_commit方法
                self._commit(
                    task,
                    success_msg=f"任务更新成功 - ID: {task_id}, 任务名称: {task.name}",
                    fail_msg="任务更新失败",
                    operation="task_update",
                    extra={"updated_fields": updated_fields}
                )

            return self._serialize_task(task)

        except IntegrityError as e:
            if "uq_task_project_name" in str(e):
                raise ParamException(f"项目下已存在同名任务: {name}")
            raise
