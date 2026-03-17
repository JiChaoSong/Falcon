#!/project/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-03 15:16 
    Name  :     project_service.py
    Desc  :     
--------------------------------------
"""
import math
from typing import Optional, Dict, Any, List, Text

from sqlalchemy import Select, false, true, Delete, text, String
from sqlalchemy.exc import SQLAlchemyError

from app.core.exception import ParamException
from app.decorators.audit import get_current_user
from app.models import Project, Users, ProjectMember, MemberRoleEnum
from app.schemas import project as schemas
from app.services.access_control_service import AccessControlService
from app.services.base_service import BaseService, ModelType
from app.services.project_member_service import ProjectMemberService
from sqlalchemy.orm import Session

import logging


class ProjectService(BaseService[Project, schemas.ProjectCreate, schemas.ProjectUpdate]):

    def __init__(self, db: Session):
        super().__init__(db, Project)
        self.logger = logging.getLogger(__name__)
        self.access_control = AccessControlService(db)
        self.member_service = ProjectMemberService(db)

    def _get_user_by_id(self, user_id: int) -> Users:
        """根据ID获取用户"""
        user = self.db.execute(
            Select(Users).where(
                Users.id == user_id,
                Users.is_deleted == false()
            )
        ).scalar_one_or_none()

        if not user:
            self.logger.error(f'用户不存在:{user_id}')
            raise ParamException('用户不存在')

        return user

    def _get_project_by_id(self, project_id: int) -> Project:
        """根据项目id获取项目"""
        project = self.db.execute(
            Select(Project).where(
                Project.id == project_id,
                Project.is_deleted == false()
            )
        ).scalar_one_or_none()

        if not project:
            self.logger.error(f'项目不存在:{project_id}')
            raise ParamException('项目不存在')

        return project

    def _validate_project_name_unique(self, name: str, exclude_project_id: int = None) -> None:
        query = Select(Project).where(
            Project.name == name,
            Project.is_deleted == false()
        )
        if exclude_project_id:
            query = query.where(Project.id == exclude_project_id)

        existing_project = self.db.execute(query).scalar_one_or_none()

        if  existing_project:
            raise ParamException('项目名称已存在')

    def _add_project_owner(self, project_id: int, owner_id: int, owner_name:str) -> None:
        """添加项目负责人"""
        # 检查是否已经是项目成员
        existing_member = self.db.execute(
            Select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.member_id == owner_id,
                ProjectMember.is_deleted == false()
            )
        ).scalar_one_or_none()

        if existing_member:
            # 如果已经是成员，更新角色为OWNER
            existing_member.member_role = MemberRoleEnum.OWNER
            existing_member.is_active = True
        else:
            # 添加新的项目成员作为负责人
            project_owner = ProjectMember(
                project_id=project_id,
                member_id=owner_id,
                member_name=owner_name,
                member_role=MemberRoleEnum.OWNER,
                is_active=True
            )
            self.db.add(project_owner)

    def _update_project_owner(
        self,
        project_id: int,
        new_owner_id: Optional[int] = None,
        new_owner_name: Optional[str] = None,
    ) -> None:
        """更新项目负责人"""
        if new_owner_id is None:
            return  # 没有指定新的负责人，保持原状

        # 查找当前项目的负责人
        current_owner = self.db.execute(
            Select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.member_role == MemberRoleEnum.OWNER,
                ProjectMember.is_active == true(),
                ProjectMember.is_deleted == false()
            )
        ).scalar_one_or_none()

        if current_owner:
            # 如果当前负责人存在且不同，则更新
            if current_owner.member_id != new_owner_id:
                # 将当前负责人降级为VIEWER（或根据业务逻辑调整）
                current_owner.member_role = MemberRoleEnum.VIEWER

                # 添加新的负责人
                self._add_project_owner(project_id, new_owner_id, new_owner_name or current_owner.member_name)
        else:
            # 没有找到负责人，直接添加新的负责人
            self._add_project_owner(project_id, new_owner_id, new_owner_name or "")

    def _delete_project_member(self, project_id: int) -> None:
        """删除项目成员"""

        user_id, username = get_current_user()

        # 查找当前项目的负责人
        project_owner = self.db.execute(
            Select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.is_deleted == false(),
                ProjectMember.member_id == user_id,
                ProjectMember.member_role == MemberRoleEnum.OWNER,
            )
        ).scalar_one_or_none()

        if not project_owner:
            raise ParamException('当前用户不是项目负责人, 无法删除')

        if not project_owner.is_active:
            raise ParamException('当前用户项目状态不可用, 无法删除')

        try:
            self.db.execute(
                Delete(ProjectMember).where(
                    ProjectMember.project_id == project_id,
                )
            )
        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.warning(f"删除场景用例关联失败: {str(e)}")


    def get(self, id: int) -> Optional[ModelType]:
        self.access_control.ensure_project_view_access(id)

        project =  self._get_project_by_id(id)

        # 获取项目负责人id
        owner = self.db.execute(
            Select(ProjectMember).where(
                ProjectMember.project_id == id,
                ProjectMember.member_role == MemberRoleEnum.OWNER,
                ProjectMember.is_active == true(),
                ProjectMember.is_deleted == false()
            )
        ).scalar_one_or_none()

        # 获取项目负责人信息
        if not owner:
            raise ParamException('项目负责人不存在')

        user = self._get_user_by_id(owner.member_id)

        result = project.to_dict()
        if user:
            result['owner_id'] = user.id
            result['owner_name'] = user.name
        result['members'] = self.member_service.list(id)
        return result

    def delete(self, id: int) -> Optional[bool]:
        self.access_control.ensure_project_owner_access(id)

        project = self._get_project_by_id(id)

        if getattr(project, 'is_deleted', False):
            self.logger.warning(
                f"项目已被删除 - ID: {id}",
                extra={
                    "project_id": id,
                    "operation": "project_delete",
                    "error": "项目已被删除"
                }
            )
            raise ParamException("项目已被删除")

        # 检查模型是否支持软删除
        if not hasattr(project, 'is_deleted'):
            self.logger.warning(
                f"模型不支持软删除 - 模型: {self.model_class.__name__}, ID: {id}",
                extra={
                    "model": f'{self.model_class.__name__}',
                    "operation": "project_delete",
                    "error": "模型不支持软删除"
                }
            )
            raise ParamException(f"{self.model_class.__name__}不支持删除")


        project.soft_delete()

        self._commit(
            project,
            success_msg=f"项目删除成功 - 项目名称: {project.name}",
            fail_msg=f"项目{project.name}删除失败",
            operation="project_delete"
        )

        if project.is_deleted:
            self._delete_project_member(project_id=id)

        self.db.commit()
        return True


    def create(self, data: schemas.ProjectCreate) -> Dict[str, Any] | None:
        current_user = self.access_control.get_current_user()

        create_data = data.model_dump()

        name = create_data.get('name')

        # 提取负责人信息
        owner_id = create_data.pop('owner_id', None)
        owner_name = create_data.pop('owner_name', None)
        if not owner_id:
            raise ParamException("项目负责人不能为空")
        if not current_user.is_admin and owner_id != current_user.id:
            raise ParamException("普通用户只能将自己设置为项目负责人")

        self._validate_project_name_unique(name)

        new_project = Project(**create_data)

        self.db.add(new_project)
        self.db.flush()  # 获取新项目的ID

        # 添加项目负责人
        try:
            self._add_project_owner(new_project.id, owner_id, owner_name)
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"添加项目负责人失败: {str(e)}")
            raise ParamException("添加项目负责人失败")

        self._commit(
            new_project,
            success_msg=f"项目创建成功 - 项目名称: {name}",
            fail_msg=f"项目{name}创建失败",
            operation="project_create"
        )
        result = new_project.to_dict()
        result['owner_id'] = owner_id
        result['owner_name'] = owner_name

        return result

    def update(self, data: schemas.ProjectUpdate) -> Dict[str, Any] | None:

        update_data = data.model_dump(exclude_unset=True)
        # 提取负责人信息
        owner_id = update_data.pop('owner_id', None)
        owner_name = update_data.pop('owner_name', None)

        name = update_data.get('name')
        project_id = update_data.get('id')
        self.access_control.ensure_project_manage_access(project_id)

        project = self._get_project_by_id(project_id)

        if name and name != project.name:
            self._validate_project_name_unique(name, project_id)

        for field, value in update_data.items():
            # 跳过不允许直接更新的字段
            if field in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by'
                         , 'is_deleted', 'created_by_name', 'updated_by_name', 'deleted_by_name']:
                continue

            if hasattr(project, field) and getattr(project, field) != value:
                setattr(project, field, value)

        # 更新项目负责人（如果提供了新的负责人）
        if owner_id is not None:
            if owner_name is None:
                owner = self._get_user_by_id(owner_id)
                owner_name = owner.name
            self._update_project_owner(project_id, owner_id, owner_name)

        self._commit(
            project,
            success_msg=f"项目更新成功 - ID: {project_id}, 项目名称: {name}",
            fail_msg="项目更新失败",
            operation="project_update",
            extra={"updated_fields": list(update_data.keys())}
        )

        # 获取当前的负责人
        current_owner = self.db.execute(
            Select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.member_role == MemberRoleEnum.OWNER,
                ProjectMember.is_active == true(),
                ProjectMember.is_deleted == false(),
            )
        ).scalar_one_or_none()

        result = project.to_dict()
        result['owner_id'] = current_owner.member_id if current_owner else None
        result['owner_name'] = current_owner.member_name if current_owner else owner_name

        return result

    def list(self, page: int = 1, page_size: int = 10, **kwargs):

        query_data = kwargs.copy()
        accessible_project_ids = self.access_control.get_accessible_project_ids()

        # 构建基础查询
        base_query = """
                     SELECT p.id, 
                            p.name, 
                            p.description, 
                            p.status, 
                            p.priority, 
                            p.tags, 
                            p.created_at, 
                            p.created_by_name, 
                            p.created_by, 
                            p.updated_at, 
                            p.updated_by, 
                            p.updated_by_name, 
                            p.is_deleted, 
                            m.member_id as owner_id, 
                            m.member_name as owner_name,
                            COALESCE(scenario_counts.scenario_count, 0) as scenario_count,
                            COALESCE(task_counts.task_count, 0) as task_count,
                            t.last_run_time
                     FROM projects p
                    LEFT JOIN (
                            -- 统计每个项目的场景数量
                        SELECT project_id, COUNT(*) as scenario_count
                        FROM scenarios
                        WHERE is_deleted = false
                        GROUP BY project_id
                    ) scenario_counts ON p.id = scenario_counts.project_id
                    LEFT JOIN (
                        -- 统计每个项目的任务数量
                        SELECT project_id, COUNT(*) as task_count
                        FROM tasks
                        WHERE is_deleted = false
                        GROUP BY project_id
                    ) task_counts ON p.id = task_counts.project_id 
                    
                    LEFT JOIN (
                     -- 查询最后一次运行的任务时间
                         SELECT project_id, start_time as last_run_time
                         FROM tasks
                         WHERE is_deleted = false
                             AND status IN ('COMPLETED', 'FAILED')
                         ORDER BY start_time DESC LIMIT 1
                     ) t ON p.id = t.project_id 
                     INNER JOIN project_members m ON m.project_id = p.id 
                         AND m.member_role = 'OWNER'
                         AND m.is_active = true
                         AND m.is_deleted = false
                     WHERE p.is_deleted = false 
                    
                     """

        count_query = """
                     SELECT COUNT(*) as total
                     FROM projects p      
                     INNER JOIN project_members m ON m.project_id = p.id
                         AND m.member_role = 'OWNER'
                         AND m.is_active = true
                         AND m.is_deleted = false
                     WHERE p.is_deleted = false 
                    
                     """
        tags = query_data.pop('tags', [])
        member_id = query_data.pop('owner_id', None)
        member_name = query_data.pop('owner_name', None)

        query_data['member_id'] = member_id
        query_data['member_name'] = member_name

        # 标签查询
        if tags and len(tags) > 0:
            # 包含任意一个标签
            tag_conditions = []
            for tag in tags:
                tag_conditions.append(f"""JSON_CONTAINS(p.tags, '"{tag}"')""")

            if tag_conditions:
                base_query += " AND (" + " OR ".join(tag_conditions) + ')'
                count_query += " AND (" + " OR ".join(tag_conditions) + ')'

        valid_query = {key: val for key, val in query_data.items() if val is not None and val != ''}

        if accessible_project_ids is not None:
            if not accessible_project_ids:
                return {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': 0,
                    'total': 0,
                    'results': [],
                }
            project_ids = ",".join(str(project_id) for project_id in accessible_project_ids)
            base_query += f" AND p.id IN ({project_ids})"
            count_query += f" AND p.id IN ({project_ids})"

        for field_name, value in valid_query.items():
            if value is  None:
                continue
            # 检查字段是否存在
            if hasattr(Project, field_name) and field_name != 'tags':
                field = getattr(Project, field_name)
                if isinstance(field.type, (String, Text)):

                    base_query += f" AND p.{field_name} LIKE '%{value}%'"
                    count_query += f" AND p.{field_name} LIKE '%{value}%'"
                elif field_name in {"status", "priority"}:
                    normalized_value = str(value).lower()
                    base_query += f" AND LOWER(p.{field_name}) = '{normalized_value}'"
                    count_query += f" AND LOWER(p.{field_name}) = '{normalized_value}'"
                else:
                    base_query += f' AND p.{field_name} = {value}'
                    count_query += f' AND p.{field_name} = {value}'

            if hasattr(ProjectMember, field_name):
                field = getattr(ProjectMember, field_name)
                if isinstance(field.type, (String, Text)):
                    base_query += f" AND m.{field_name} LIKE '%{value}%'"
                    count_query += f" AND m.{field_name} LIKE '%{value}%'"
                else:
                    base_query += f' AND m.{field_name} = {value}'
                    count_query += f' AND m.{field_name} = {value}'

        # self.logger.warning(base_query)

        order_query = f" ORDER BY p.created_at DESC"

        limit_offset_query = f" LIMIT {page_size} OFFSET {(page - 1) * page_size};"

        base_query += order_query + limit_offset_query

        total = self.db.execute(text(count_query)).scalar()
        result = self.db.execute(text(base_query))

        columns = result.keys()
        results = [dict(zip(columns, row)) for row in result]

        return {
            'page': page,
            'page_size': page_size,
            'total_pages': math.ceil(total / page_size) if total != 0 else 0,
            'total': total,
            'results': results,
        }
