# app/api/v1/case.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.response import SuccessResponse
from app.db import get_db
from app.schemas import case as schemas
from app.services.case_service import CaseService

router = APIRouter(prefix="/case", tags=["Case"])


@router.post("/list", response_model=schemas.CaseListResponse)
async def case_list(data:schemas.QueryCaseList, db: Session = Depends(get_db),):


    case_service = CaseService(db)

    cases = case_service.list(**data.model_dump())

    return SuccessResponse(data=cases)

@router.post("/info", response_model=schemas.CaseInfoResponse)
async def case_info(data: schemas.QueryCaseOne, db: Session = Depends(get_db),):

    case_service = CaseService(db)

    cases = case_service.get(**data.model_dump())

    return SuccessResponse(data=cases)


@router.post("/delete", response_model=schemas.BaseResponse)
async def case_delete(data: schemas.QueryCaseOne, db: Session = Depends(get_db)):

    case_service = CaseService(db)

    case_service.delete(**data.model_dump())

    return SuccessResponse(data=None)

@router.post("/create", response_model=schemas.CaseInfoResponse)
async def case_create(data: schemas.CaseCreate, db: Session = Depends(get_db)):

    case_service = CaseService(db)

    cases = case_service.create(**data.model_dump())

    return SuccessResponse(data=cases)

@router.post("/update", response_model=schemas.CaseInfoResponse)
async def case_update(data: schemas.CaseUpdate, db: Session = Depends(get_db)):

    case_service = CaseService(db)

    cases = case_service.update(**data.model_dump())

    return SuccessResponse(data=cases)

@router.post("/config", response_model=schemas.CaseInfoResponse)
async def case_config(data: schemas.CaseConfig, db: Session = Depends(get_db)):

    case_service = CaseService(db)

    cases = case_service.config(**data.model_dump())

    return SuccessResponse(data=cases)