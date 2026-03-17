
from datetime import datetime
from typing import Optional, Dict
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLAlchemyEnum, JSON
from sqlalchemy.orm import relationship, mapped_column, Mapped
from app.models import BaseModel

class CaseStatusEnum(str, Enum):
    ACTIVE = "active"      # 在用状态（可执行）
    INACTIVE = "inactive"  # 停用状态（暂不执行）
    ARCHIVED = "archived"  # 归档状态（历史用例）
    DRAFT = "draft"        # 草稿状态（未完成）

    @property
    def label(self):
        labels = {
            self.ACTIVE: "启用中",
            self.INACTIVE: "已停用",
            self.ARCHIVED: "已废弃",
            self.DRAFT: "草稿"
        }
        return labels[self]

class Case(BaseModel):
    __tablename__ = "cases"


    # 基础信息
    name: Mapped[str] = mapped_column(String(255), comment="用例名称")
    type: Mapped[str] = mapped_column(String(20), comment="用例类型")
    method: Mapped[Optional[str]] = mapped_column(String(10), comment="请求方法")
    url: Mapped[str] = mapped_column(String(500), comment="请求URL")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="用例描述")
    status: Mapped[CaseStatusEnum] = mapped_column(
        SQLAlchemyEnum(CaseStatusEnum, name="status"),
        comment="用例状态",
        default=CaseStatusEnum.DRAFT
    )
    project_id:Mapped[int] = mapped_column(Integer, nullable=False, comment='所属项目id')
    project: Mapped[str] = mapped_column(String(50), comment="所属项目名称")
    headers: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="请求头")
    body:Mapped[Optional[str]] = mapped_column(Text, nullable=True,comment="请求体")
    expected_status: Mapped[str] = mapped_column(String(10), nullable=True,comment="预期响应状态码")
    expected_response_time: Mapped[int] = mapped_column(Integer, nullable=True,comment="预期响应时间（ms）")
    assertion:Mapped[Optional[str]] = mapped_column(Text, nullable=True,comment='断言')
    pre_request_script: Mapped[Optional[str]] = mapped_column(Text, nullable=True,comment='前置脚本')
    post_request_script: Mapped[Optional[str]] = mapped_column(Text, nullable=True,comment='后置脚本')
    # 类型：Optional[Dict[str, str]] 标注为「字符串键值对」，JSON类型存储
    extract: Mapped[Optional[Dict[str, str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="响应数据提取规则：{变量名: 提取路径}，默认使用jsonpath提取方式"
    )