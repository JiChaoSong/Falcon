from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db import Base
from app.models import BaseModel


class ScenarioStatusEnum(str, Enum):
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


class Scenario(BaseModel):
    __tablename__ = "scenarios"


    name: Mapped[str] = mapped_column(String(255), comment="场景名称")
    project_id:Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属项目id')
    project: Mapped[str] = mapped_column(String(50), nullable=False, comment="所属项目名称")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="用例描述")
    status: Mapped[ScenarioStatusEnum] = mapped_column(
        SQLAlchemyEnum(ScenarioStatusEnum, name="status"),
        comment="场景状态",
        default=ScenarioStatusEnum.DRAFT
    )
    total_testcases: Mapped[int] = mapped_column(Integer, default=0, comment="关联用例总数")
    last_run: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,comment="最后运行时间")

class ScenarioCase(BaseModel):
    __tablename__ = "scenario_cases"

    scenario_id:Mapped[int] = mapped_column(BigInteger, comment='场景id')
    case_id:Mapped[int] = mapped_column(BigInteger, comment='用例id')
    order:Mapped[int] = mapped_column(Integer, default=0, comment='序号')
    weight:Mapped[int] = mapped_column(Integer, default=0, comment='权重')
