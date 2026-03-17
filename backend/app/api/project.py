# app/api/v1/project_service.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.response import SuccessResponse
from app.db import get_db
from app import models
from app.schemas import project as schemas
from app.services.project_member_service import ProjectMemberService
from app.services.project_service import ProjectService

router = APIRouter(prefix="/project", tags=["Project"])

@router.post("/list", response_model=schemas.ProjectListResponse)
async def project_list(data:schemas.QueryProjectList, db: Session = Depends(get_db),):


    project_service = ProjectService(db)

    projects = project_service.list(**data.model_dump())

    return SuccessResponse(data=projects)

@router.post("/info", response_model=schemas.ProjectInfoResponse)
async def project_info(data: schemas.QueryProjectOne, db: Session = Depends(get_db),):

    project_service = ProjectService(db)

    projects = project_service.get(**data.model_dump())

    return SuccessResponse(data=projects)


@router.post("/delete", response_model=schemas.BaseResponse)
async def project_delete(data: schemas.QueryProjectOne, db: Session = Depends(get_db)):

    project_service = ProjectService(db)

    project_service.delete(**data.model_dump())

    return SuccessResponse(data=None)

@router.post("/create", response_model=schemas.ProjectInfoResponse)
async def project_create(data: schemas.ProjectCreate, db: Session = Depends(get_db)):
    print(data.model_dump())
    project_service = ProjectService(db)

    projects = project_service.create(data)

    return SuccessResponse(data=projects)

@router.post("/update", response_model=schemas.ProjectInfoResponse)
async def project_update(data: schemas.ProjectUpdate, db: Session = Depends(get_db)):

    project_service = ProjectService(db)

    projects = project_service.update(data)

    return SuccessResponse(data=projects)


@router.post("/member/list", response_model=schemas.ProjectMemberListResponse)
async def project_member_list(data: schemas.QueryProjectOne, db: Session = Depends(get_db)):

    member_service = ProjectMemberService(db)

    members = member_service.list(data.id)

    return SuccessResponse(data=members)


@router.post("/member/add", response_model=schemas.BaseResponse)
async def project_member_add(data: schemas.ProjectMemberCreate, db: Session = Depends(get_db)):

    member_service = ProjectMemberService(db)

    member = member_service.add_member(data.project_id, data.member_id, data.member_role)

    return SuccessResponse(data=member)


@router.post("/member/update-role", response_model=schemas.BaseResponse)
async def project_member_update_role(data: schemas.ProjectMemberUpdate, db: Session = Depends(get_db)):

    member_service = ProjectMemberService(db)

    member = member_service.update_member_role(data.project_id, data.member_id, data.member_role)

    return SuccessResponse(data=member)


@router.post("/member/remove", response_model=schemas.BaseResponse)
async def project_member_remove(data: schemas.ProjectMemberRemove, db: Session = Depends(get_db)):

    member_service = ProjectMemberService(db)

    member_service.remove_member(data.project_id, data.member_id)

    return SuccessResponse(data=None)
