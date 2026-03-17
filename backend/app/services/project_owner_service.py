#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-05 16:27 
    Name  :     project_owner_service.py
    Desc  :     
--------------------------------------
"""
from typing import List, Optional
from sqlalchemy import Select
from sqlalchemy.orm import Session

from app.models import ProjectMember, MemberRoleEnum
from app.core.exception import ParamException


class ProjectOwnerService:
    """项目负责人管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_project_owner(self, project_id: int) -> Optional[ProjectMember]:
        """获取项目负责人"""
        owner = self.db.execute(
            Select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.member_role == MemberRoleEnum.OWNER,
                ProjectMember.is_active == True
            )
        ).scalar_one_or_none()

        return owner

    def set_project_owner(self, project_id: int, user_id: str) -> ProjectMember:
        """设置项目负责人"""
        # 检查用户是否已经是项目成员
        existing_member = self.db.execute(
            Select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.member_id == user_id
            )
        ).scalar_one_or_none()

        if existing_member:
            # 如果是现有成员，更新角色为OWNER
            existing_member.member_role = MemberRoleEnum.OWNER
            existing_member.is_active = True
            return existing_member
        else:
            # 创建新的项目成员作为负责人
            new_owner = ProjectMember(
                project_id=project_id,
                member_id=user_id,
                member_role=MemberRoleEnum.OWNER,
                is_active=True
            )
            self.db.add(new_owner)
            return new_owner

    def transfer_ownership(self, project_id: int, new_owner_id: str, current_user_id: str) -> bool:
        """转移项目所有权"""
        # 检查当前用户是否有权限转移所有权（通常是当前负责人）
        current_owner = self.get_project_owner(project_id)

        if not current_owner:
            raise ParamException("项目没有负责人")

        if current_owner.member_id != current_user_id:
            raise ParamException("只有项目负责人可以转移所有权")

        # 将当前负责人降级为ADMIN
        current_owner.member_role = MemberRoleEnum.ADMIN

        # 设置新的负责人
        self.set_project_owner(project_id, new_owner_id)

        return True

    def get_projects_by_owner(self, user_id: str) -> List[int]:
        """获取用户负责的所有项目ID"""
        projects = self.db.execute(
            Select(ProjectMember.project_id).where(
                ProjectMember.member_id == user_id,
                ProjectMember.member_role == MemberRoleEnum.OWNER,
                ProjectMember.is_active == True
            )
        ).scalars().all()

        return list(projects)


