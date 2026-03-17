from typing import Optional

from sqlalchemy import Select, false, true
from sqlalchemy.orm import Session

from app.core.exception import ParamException
from app.decorators.audit import get_current_user
from app.models import MemberRoleEnum, ProjectMember, Users


class AccessControlService:
    def __init__(self, db: Session):
        self.db = db

    def get_current_user(self) -> Users:
        user_id, _ = get_current_user()
        if not user_id:
            raise ParamException("未获取到当前登录用户")

        user = self.db.execute(
            Select(Users).where(
                Users.id == user_id,
                Users.is_deleted == false(),
            )
        ).scalar_one_or_none()

        if not user:
            raise ParamException("当前用户不存在")

        return user

    def is_admin(self) -> bool:
        return self.get_current_user().is_admin

    def require_admin(self) -> Users:
        user = self.get_current_user()
        if not user.is_admin:
            raise ParamException("仅管理员可执行该操作")
        return user

    def get_accessible_project_ids(self) -> Optional[list[int]]:
        user = self.get_current_user()
        if user.is_admin:
            return None

        project_ids = self.db.execute(
            Select(ProjectMember.project_id).where(
                ProjectMember.member_id == user.id,
                ProjectMember.is_active == true(),
                ProjectMember.is_deleted == false(),
            )
        ).scalars().all()

        return list(project_ids)

    def can_view_project(self, project_id: int) -> bool:
        if self.is_admin():
            return True

        user = self.get_current_user()
        member = self.db.execute(
            Select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.member_id == user.id,
                ProjectMember.is_active == true(),
                ProjectMember.is_deleted == false(),
            )
        ).scalar_one_or_none()

        return member is not None

    def ensure_project_view_access(self, project_id: int) -> None:
        if not self.can_view_project(project_id):
            raise ParamException("无权限访问该项目")

    def ensure_project_manage_access(self, project_id: int) -> None:
        if self.is_admin():
            return

        user = self.get_current_user()
        member = self.db.execute(
            Select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.member_id == user.id,
                ProjectMember.member_role.in_([MemberRoleEnum.OWNER, MemberRoleEnum.ADMIN]),
                ProjectMember.is_active == true(),
                ProjectMember.is_deleted == false(),
            )
        ).scalar_one_or_none()

        if not member:
            raise ParamException("无权限管理该项目")

    def ensure_project_owner_access(self, project_id: int) -> None:
        if self.is_admin():
            return

        user = self.get_current_user()
        member = self.db.execute(
            Select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.member_id == user.id,
                ProjectMember.member_role == MemberRoleEnum.OWNER,
                ProjectMember.is_active == true(),
                ProjectMember.is_deleted == false(),
            )
        ).scalar_one_or_none()

        if not member:
            raise ParamException("仅项目负责人可执行该操作")
