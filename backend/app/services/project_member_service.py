from typing import Any

from sqlalchemy import Select, false, true
from sqlalchemy.orm import Session

from app.core.exception import ParamException
from app.models import MemberRoleEnum, Project, ProjectMember, Users
from app.services.access_control_service import AccessControlService


class ProjectMemberService:
    def __init__(self, db: Session):
        self.db = db
        self.access_control = AccessControlService(db)

    def _get_project(self, project_id: int) -> Project:
        project = self.db.execute(
            Select(Project).where(
                Project.id == project_id,
                Project.is_deleted == false(),
            )
        ).scalar_one_or_none()
        if not project:
            raise ParamException("项目不存在")
        return project

    def _get_user(self, user_id: int) -> Users:
        user = self.db.execute(
            Select(Users).where(
                Users.id == user_id,
                Users.is_deleted == false(),
            )
        ).scalar_one_or_none()
        if not user:
            raise ParamException("用户不存在")
        return user

    def _get_member(self, project_id: int, member_id: int) -> ProjectMember:
        member = self.db.execute(
            Select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.member_id == member_id,
                ProjectMember.is_deleted == false(),
            )
        ).scalar_one_or_none()
        if not member:
            raise ParamException("项目成员不存在")
        return member

    def _serialize_member(self, member: ProjectMember) -> dict[str, Any]:
        data = member.to_dict()
        data["member_role"] = member.member_role.name if member.member_role else None
        return data

    def list(self, project_id: int) -> list[dict[str, Any]]:
        self.access_control.ensure_project_view_access(project_id)
        members = self.db.execute(
            Select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.is_deleted == false(),
            ).order_by(ProjectMember.member_role.asc(), ProjectMember.id.asc())
        ).scalars().all()
        return [self._serialize_member(member) for member in members]

    def add_member(self, project_id: int, member_id: int, member_role: MemberRoleEnum) -> dict[str, Any]:
        self.access_control.ensure_project_manage_access(project_id)
        self._get_project(project_id)
        user = self._get_user(member_id)

        if member_role == MemberRoleEnum.OWNER:
            raise ParamException("项目负责人请通过项目负责人变更流程处理")

        existing_member = self.db.execute(
            Select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.member_id == member_id,
                ProjectMember.is_deleted == false(),
            )
        ).scalar_one_or_none()

        if existing_member:
            existing_member.member_role = member_role
            existing_member.member_name = user.name
            existing_member.is_active = True
            self.db.commit()
            self.db.refresh(existing_member)
            return self._serialize_member(existing_member)

        member = ProjectMember(
            project_id=project_id,
            member_id=member_id,
            member_name=user.name,
            member_role=member_role,
            is_active=True,
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return self._serialize_member(member)

    def update_member_role(self, project_id: int, member_id: int, member_role: MemberRoleEnum) -> dict[str, Any]:
        self.access_control.ensure_project_manage_access(project_id)
        if member_role == MemberRoleEnum.OWNER:
            raise ParamException("项目负责人请通过项目负责人变更流程处理")

        member = self._get_member(project_id, member_id)
        if member.member_role == MemberRoleEnum.OWNER:
            raise ParamException("项目负责人角色不能在成员管理中修改")

        member.member_role = member_role
        member.is_active = True
        self.db.commit()
        self.db.refresh(member)
        return self._serialize_member(member)

    def remove_member(self, project_id: int, member_id: int) -> bool:
        self.access_control.ensure_project_manage_access(project_id)
        member = self._get_member(project_id, member_id)
        if member.member_role == MemberRoleEnum.OWNER:
            raise ParamException("项目负责人不能在成员管理中移除")
        member.soft_delete()
        member.is_active = False
        self.db.commit()
        return True
