from datetime import datetime
from typing import Optional, List

from sqlalchemy import BigInteger, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum as SQLAlchemyEnum, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from enum import Enum

from app.db import Base
from app.models.base import BaseModel

# =============================
# Project
# =============================

class ProjectStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

class ProjectPriorityEnum(str, Enum):
    HIGH = "high"
    LOW = "low"
    MEDIUM = "medium"


class Project(BaseModel):
    __tablename__ = "projects"

    name:Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment='项目名称')
    description: Mapped[str] = mapped_column(Text, nullable=True, comment='项目描述')
    status:Mapped[Optional[ProjectStatusEnum]] = mapped_column(
        SQLAlchemyEnum(ProjectStatusEnum),
        default=ProjectStatusEnum.ACTIVE,
        nullable=False,comment='项目状态')
    priority: Mapped[Optional[ProjectPriorityEnum]] = mapped_column(
        SQLAlchemyEnum(ProjectPriorityEnum),
        default=ProjectPriorityEnum.HIGH,
        nullable=False,
        comment='项目优先级'
    )
    tags:Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True, default=[], comment='项目标签')


class MemberRoleEnum(str, Enum):
    OWNER = "owner" # 项目负责人
    ADMIN = "admin" # 项目管理员
    DEVELOPER = "developer" # 开发人员
    TEACHER = "teacher"  # 测试人员
    VIEWER = "viewer"  # 只读查看

class ProjectMember(BaseModel):

    __tablename__ = "project_members"

    project_id:Mapped[int] = mapped_column(BigInteger, nullable=False, comment='项目id')
    member_id:Mapped[int] = mapped_column(BigInteger, nullable=False, comment='用户id')
    member_name:Mapped[str] = mapped_column(String(50), nullable=False, comment='用户名称')
    member_role:Mapped[Optional[MemberRoleEnum]] = mapped_column(
        SQLAlchemyEnum(MemberRoleEnum),
        default=MemberRoleEnum.VIEWER,
        nullable=False,
        comment='项目成员角色'
    )
    join_time: Mapped[datetime] = mapped_column(server_default=func.now(), comment="加入时间")
    is_active:Mapped[bool] = mapped_column(default=True, nullable=False, comment='是否有效')
