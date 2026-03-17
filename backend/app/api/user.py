#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-02 22:09 
    Name  :     user.py
    Desc  :     
--------------------------------------
"""
from ecdsa.test_keys import data
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.response import SuccessResponse, ExceptionResponse, FailExceptResponse
from app.db import get_db
from app.schemas import users as schemas
from app.services.user_service import UserService

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/login", response_model=schemas.UserLoginOutResponseInfo)
async def login(data: schemas.UserLogin, db: Session = Depends(get_db)):

    user_service = UserService(db=db)

    user_info_data = user_service.authenticate_user(
        username=data.username,
        password=data.password
    )

    return SuccessResponse(data=user_info_data)


@router.post('/logout', response_model=schemas.SuccessResponse)
async def logout(db: Session = Depends(get_db)):

    # user_service = UserService(db=db)

    # user_service

    return SuccessResponse(data=None)



@router.post('/create', response_model=schemas.UserInfoOne)
async def create_user(data:schemas.UserCreate, db: Session = Depends(get_db)):

    user_service = UserService(db=db)

    user = user_service.create(data)

    return SuccessResponse(data=user)



@router.post('/update', response_model=schemas.UserInfoOne)
async def update_user(data:schemas.UserUpdate, db: Session = Depends(get_db)):

    user_service = UserService(db=db)

    user = user_service.update(data)

    return SuccessResponse(data=user)



@router.post('/list', response_model=schemas.UserInfoListResponse)
async def list_users(data: schemas.UserInfoListQuery, db: Session = Depends(get_db)):

    user_service = UserService(db=db)

    users = user_service.list(**data.model_dump())

    data_list = [
        user.to_dict(exclude=['password'])
        for user in users["results"]
    ]

    users['results'] = data_list

    return SuccessResponse(data=users)

@router.post('/detail', response_model=schemas.UserInfoOne)
async def get_user_info(data:schemas.GetUserInfo, db: Session = Depends(get_db)):

    user_service = UserService(db=db)

    user = user_service.get(**data.model_dump())

    return SuccessResponse(data=user.to_dict(exclude=['password']))

@router.post('/delete', response_model=schemas.BaseResponse)
async def delete_user(data:schemas.GetUserInfo, db: Session = Depends(get_db)):

    user_service = UserService(db=db)

    user_service.delete(**data.model_dump())

    return SuccessResponse(data=None)

@router.post('/info', response_model=schemas.UserInfoOne)
async def get_user_info(request: Request, db: Session = Depends(get_db)):

    user_service = UserService(db=db)

    user = user_service.info(request)

    return SuccessResponse(data=user)