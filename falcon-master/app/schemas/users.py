#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-02 15:07
    Name  :     users
    Desc  :     
--------------------------------------
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.base import BaseSchema, BaseListSchema, BaseQuery
from app.schemas.response import BaseResponse, SuccessResponse


class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    is_active: bool = True
    is_admin: bool = False

class UserUpdate(BaseModel):
    id: int
    username: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    is_active: bool | None = None
    is_admin: bool | None = None

class UserInfo(BaseSchema):
    username: str
    name:str
    email: str | None
    phone: str | None
    avatar: str | None
    is_active: bool
    is_admin: bool
    last_login_at: datetime | None = None


class UserLogin(BaseModel):
    username: str
    password: str

class UserLogout(UserInfo):
    access_token: str
    token_type: str
    expires_in: int


class UserInfoListQuery(BaseQuery):

    username: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    page: int = 1
    page_size: int = 10


class ResetUserPassword(BaseModel):
    id: int
    password: str


class UserOption(BaseModel):
    id: int
    username: str
    name: str


class UserOptionListResponse(BaseResponse):
    data: Optional[List[UserOption]] = None

class UserInfoList(BaseListSchema):

    results: List[UserInfo]# 数据列表

class UserInfoOne(BaseResponse):

    data: Optional[UserInfo] = None

class UserInfoListResponse(BaseResponse):

    data: Optional[UserInfoList] = None

class UserLoginOutResponseInfo(BaseResponse):

    data: Optional[UserLogout] = None

class GetUserInfo(BaseModel):
    id: int
