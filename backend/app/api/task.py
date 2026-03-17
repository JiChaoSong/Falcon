# app/api/v1/task_run.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.response import SuccessResponse
from app.db import get_db
from app.schemas import task as schemas
from app.services.task_service import TaskService

router = APIRouter(prefix="/task", tags=["Task"])

@router.post("/list", response_model=schemas.TaskListResponse)
async def task_list(data:schemas.QueryTaskList, db: Session = Depends(get_db),):


    task_service = TaskService(db)

    tasks = task_service.list(**data.model_dump())

    return SuccessResponse(data=tasks)

@router.post("/info", response_model=schemas.TaskInfoResponse)
async def task_info(data: schemas.QueryTaskOne, db: Session = Depends(get_db),):

    task_service = TaskService(db)

    tasks = task_service.get(**data.model_dump())

    return SuccessResponse(data=tasks)


@router.post("/delete", response_model=schemas.BaseResponse)
async def task_delete(data: schemas.QueryTaskOne, db: Session = Depends(get_db)):

    task_service = TaskService(db)

    task_service.delete(**data.model_dump())

    return SuccessResponse(data=None)

@router.post("/create", response_model=schemas.TaskInfoResponse)
async def task_create(data: schemas.TaskCreate, db: Session = Depends(get_db)):

    task_service = TaskService(db)

    tasks = task_service.create(data)

    return SuccessResponse(data=tasks)

@router.post("/update", response_model=schemas.TaskInfoResponse)
async def task_update(data: schemas.TaskUpdate, db: Session = Depends(get_db)):

    task_service = TaskService(db)

    tasks = task_service.update(data)

    return SuccessResponse(data=tasks)
