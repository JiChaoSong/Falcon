from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import SuccessResponse
from app.db import get_db
from app.schemas import worker as schemas
from app.services.worker_registry_service import WorkerRegistryService


router = APIRouter(prefix="/worker", tags=["Worker"])


@router.post("/list", response_model=schemas.WorkerListResponse)
async def worker_list(data: schemas.WorkerQuery, db: Session = Depends(get_db)):
    service = WorkerRegistryService(db)
    result = service.list(**data.model_dump())
    return SuccessResponse(data=result)


@router.post("/info", response_model=schemas.WorkerInfoResponse)
async def worker_info(data: schemas.WorkerInfoQuery, db: Session = Depends(get_db)):
    service = WorkerRegistryService(db)
    result = service.info(data.worker_id)
    return SuccessResponse(data=result)


@router.post("/update", response_model=schemas.WorkerInfoResponse)
async def worker_update(data: schemas.WorkerUpdateRequest, db: Session = Depends(get_db)):
    service = WorkerRegistryService(db)
    result = service.update(**data.model_dump())
    return SuccessResponse(data=result)
