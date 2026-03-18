#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-02 11:37
    Name  :     user
    Desc  :     
--------------------------------------
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import validates, Mapped, mapped_column
from passlib.context import CryptContext

from app.core.exception import ParamException
from app.db import Base
from app.models.base import BaseModel
from app.utils.time_utils import utc_now

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Users(BaseModel):

    __tablename__ = "users"
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="用户名，用于登录"
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment='名称, 用户登录后展示')
    password:Mapped[str] = mapped_column(String(255), nullable=False, comment='用户密码')
    email:Mapped[str] = mapped_column(String(100), nullable=True, comment='邮箱')
    phone:Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="手机号")
    avatar:Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="头像")
    is_active:Mapped[bool] = mapped_column(Boolean, default=True, comment="用户状态")
    is_admin:Mapped[bool] = mapped_column(Boolean, default=False, comment="是否超管")
    last_login_at:Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), comment='最后登录时间')

    @validates('username')
    def validate_username(self, key: str, username: str) -> str:
        """验证用户名格式"""
        if len(username) < 3:
            raise ParamException("用户名至少需要3个字符")

        if len(username) > 50:
            raise ParamException("用户名最多50个字符")

        # 只允许字母、数字、下划线和连字符
        if not username.replace('_', '').replace('-', '').isalnum():
            raise ParamException("用户名只能包含字母、数字、下划线和连字符")

        # 不能以数字开头
        if username[0].isdigit():
            raise ParamException("用户名不能以数字开头")

        return username  # 统一转为小写

    @validates('password')
    def validate_password(self, key: str, password: str) -> str:
        """验证密码"""

        # 如果已经是 hash，就直接放行
        if password.startswith("$2b$"):
            return password

        if not password:
            raise ParamException('密码不能为空')

        if len(password) < 8:
            raise ParamException('密码至少需要8个字符')

        # 密码强度验证
        if not self._validate_password_strength(password):
            raise ParamException("密码强度不足，必须包含字母和数字")

        return password

    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login_at = utc_now()

    def set_password(self, password: str):

        # 生成密码哈希
        self.password = pwd_context.hash(password)

    def verify_password(self, password: str):
        return pwd_context.verify(password, self.password)

    @staticmethod
    def _validate_password_strength(password: str) -> bool:
        """
        验证密码强度

        Args:
            password: 明文密码

        Returns:
            True 如果密码强度足够
        """
        # 至少8个字符
        if len(password) < 8:
            return False

        # 包含字母和数字
        has_letter = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)

        if not (has_letter and has_digit):
            return False

        return True
