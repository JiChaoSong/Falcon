#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-02 15:01
    Name  :     user_service
    Desc  :     
--------------------------------------
"""
from datetime import datetime
from typing import Optional, Any, Tuple, Dict

from fastapi import HTTPException, Request
from sqlalchemy import Select, insert, false
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exception import ParamException, TokenException
from app.core.security import verify_access_token, create_access_token, refresh_access_token
from app.decorators.audit import with_user_context
from app.schemas.users import UserUpdate, UserCreate
from app.services.base_service import BaseService, CreateSchemaType, ModelType
from app.models.users import Users
import logging

class UserService(BaseService[Users, UserCreate, UserUpdate]):

    def __init__(self, db: Session):
        super().__init__(db, Users)
        self.logger = logging.getLogger(__name__)

    def _validate_user_update(self, user_id: int, username: str = None,
                              email: str = None, phone: str = None) -> None:
        """
        验证用户更新数据的唯一性

        Args:
            user_id: 当前用户ID
            username: 新用户名
            email: 新邮箱
            phone: 新手机号
        """
        # 验证用户名
        if username:
            self._validate_username_unique(username, user_id)

        # 验证邮箱
        if email and email != '':
            self._validate_email_unique(email, user_id)

        # 验证手机号
        if phone and phone != '':
            self._validate_phone_unique(phone, user_id)

    def _validate_username_unique(self, username: str, exclude_user_id: int = None) -> None:
        """验证用户名唯一性"""
        query = Select(Users).where(
            Users.username == username,
            Users.is_deleted == false()
        )

        if exclude_user_id:
            query = query.where(Users.id != exclude_user_id)

        existing_user = self.db.execute(query).scalar_one_or_none()

        if existing_user:
            raise ParamException("用户名已被使用")

    def _validate_email_unique(self, email: str, exclude_user_id: int = None) -> None:
        """验证邮箱唯一性"""
        query = Select(Users).where(
            Users.email == email,
            Users.is_deleted == false()
        )

        if exclude_user_id:
            query = query.where(Users.id != exclude_user_id)

        existing_user = self.db.execute(query).scalar_one_or_none()

        if existing_user:
            raise ParamException("邮箱已被使用")

    def _validate_phone_unique(self, phone: str, exclude_user_id: int = None) -> None:
        """验证手机号唯一性"""
        query = Select(Users).where(
            Users.phone == phone,
            Users.is_deleted == false()
        )

        if exclude_user_id:
            query = query.where(Users.id != exclude_user_id)

        existing_user = self.db.execute(query).scalar_one_or_none()

        if existing_user:
            raise ParamException("手机号已被使用")

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

    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        user = self.db.query(Users).filter(Users.username == username,Users.is_deleted == False).first()

        if not user:
            raise ParamException('用户名或密码错误')

        if not user.is_active:
            raise ParamException('用户已停用')

        if not user.verify_password(password):
            raise ParamException('用户名或密码错误')

        user.update_last_login()

        self.db.commit()
        self.logger.info(user.to_dict())
        token = self._create_user_tokens(user)

        user_info = {
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'avatar': user.avatar,
            'is_admin': user.is_admin,
            'is_active': user.is_active,
            'created_at': user.created_at,
            'created_by_name': user.created_by_name,
            'updated_by_name': user.updated_by_name,
            'updated_at': user.updated_at,
            'created_by': user.created_by,
            'updated_by': user.updated_by,
            'is_deleted': user.is_deleted,
            **token
        }

        return user_info

    def _create_user_tokens(self, user: Users) -> Dict[str, Any]:
        """
        为用户创建令牌

        Args:
            user: 用户对象

        Returns:
            令牌字典
        """
        token_data = {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
        }
        self.logger.info(token_data)
        access_token = create_access_token(token_data)
        refresh_token = refresh_access_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    def create(self, obj_in: CreateSchemaType) -> Dict[str, Any] | None:

        query_params = obj_in.model_dump(exclude_unset=True)

        username = query_params.get('username')
        password = query_params.get('password')
        email = query_params.get('email')
        phone = query_params.get('phone')

        # 验证必填字段
        if not username:
            raise ParamException("用户名不能为空")

        if not password:
            raise ParamException("密码不能为空")

        # ===== 校验逻辑不变 =====
        user = self.db.execute(
            Select(Users).where(
                Users.username == username,
                Users.is_deleted == false()
            )
        ).scalar_one_or_none()

        if user:
            raise ParamException("用户名已存在")

        if email:
            email_user = self.db.execute(
                Select(Users).where(
                    Users.email == email,
                    Users.is_deleted == false()
                )
            ).scalar_one_or_none()
            if email_user:
                raise ParamException('邮箱已被使用')

        if phone:
            phone_user = self.db.execute(
                Select(Users).where(
                    Users.phone == phone,
                    Users.is_deleted == false()
                )
            ).scalar_one_or_none()
            if phone_user:
                raise ParamException('手机号已被使用')

        query_params.pop('password', None)

        new_user = Users(**query_params)

        # 3. 使用set_password方法设置加密后的密码
        new_user.set_password(password)

        self.db.add(new_user)

        self._commit(
            new_user,
            success_msg=f"用户创建成功 - 用户名: {username}",
            fail_msg=f"用户{username}创建失败",
            operation="user_create"
        )

        return new_user.to_dict(exclude=['password'])


    def update(self,  obj_in: UserUpdate) -> Dict[str, Any] | None:

        update_data = obj_in.model_dump(exclude_unset=True)
        user_id = update_data.get('id')
        # 获取用户对象
        user = self._get_user_by_id(user_id)

        # 验证唯一性
        self._validate_user_update(
            user_id=user_id,
            username=update_data.get('username'),
            email=update_data.get('email'),
            phone=update_data.get('phone')
        )

        # 更新字段
        for field, value in update_data.items():
            # 跳过不允许直接更新的字段
            if field in ['id', 'password', 'created_at', 'updated_at', 'created_by', 'updated_by'
                         , 'is_deleted', 'created_by_name', 'updated_by_name', 'deleted_by_name']:
                continue

            if hasattr(user, field) and getattr(user, field) != value:
                setattr(user, field, value)

        self._commit(
            user,
            success_msg=f"用户更新成功 - ID: {user_id}",
            fail_msg="用户更新失败",
            operation="user_update",
            extra={"updated_fields": list(update_data.keys())}
        )
        return user.to_dict(exclude=['password'])

    def get(self, id: int) -> Optional[ModelType]:
        """根据ID获取记录"""

        return self._get_user_by_id(id)

    def delete(self, id: int) -> Optional[bool]:

        user = self._get_user_by_id(id)

        if getattr(user, 'is_deleted', False):
            self.logger.warning(
                f"用户已被删除 - ID: {id}",
                extra={
                    "operation": "user_delete",
                    "error": "用户已被删除"
                }
            )
            raise ParamException("用户已被删除")

        # 检查模型是否支持软删除
        if not hasattr(user, 'is_deleted'):
            self.logger.warning(
                f"模型不支持软删除 - 模型: {self.model_class.__name__}, ID: {id}",
                extra={
                    "model": f'{self.model_class.__name__}',
                    "operation": "user_delete",
                    "error": "模型不支持软删除"
                }
            )
            raise ParamException(f"{self.model_class.__name__}不支持删除")


        user.soft_delete()

        # 保存到数据库
        try:
            self.db.commit()
            self.db.refresh(user)

            self.logger.info(
                f"用户删除成功 - ID: {id}",
                extra={
                    "operation": "user_delete",
                }
            )
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(f"用户删除失败 - 数据库错误: {str(e)}")
            raise ParamException("删除用户失败")

    def info(self, request:Request) -> Dict[str, Any] | None:
        token  = request.headers.get("Authorization")

        payload = verify_access_token(token)

        if not payload:
            raise TokenException()

        user = self._get_user_by_id(payload.id)

        return user.to_dict(exclude=['password'])