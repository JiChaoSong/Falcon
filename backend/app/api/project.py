# app/api/v1/project_service.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.response import SuccessResponse
from app.db import get_db
from app import models
from app.schemas import project as schemas
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

    projects = project_service.update(**data.model_dump())

    return SuccessResponse(data=projects)
