# falcon_shared/api/v1/task_run.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.response import SuccessResponse
from app.db import get_db
from app.schemas import task as schemas
from app.services.task_runtime_service import TaskRuntimeService
from app.services.task_service import TaskService

router = APIRouter(prefix="/task", tags=["Task"])

@router.post("/list", response_model=schemas.TaskListResponse)
async def task_list(data:schemas.QueryTaskList, db: Session = Depends(get_db),):


    task_service = TaskService(db)

    tasks = task_service.list(**data.model_dump(mode="json"))

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


@router.post("/run", response_model=schemas.BaseResponse)
async def task_run(data: schemas.TaskRunStartRequest, db: Session = Depends(get_db)):
    task_runtime_service = TaskRuntimeService(db)
    result = task_runtime_service.run(data.task_id)
    return SuccessResponse(data=result)


@router.post("/stop", response_model=schemas.BaseResponse)
async def task_stop(data: schemas.TaskRunStopRequest, db: Session = Depends(get_db)):
    task_runtime_service = TaskRuntimeService(db)
    result = task_runtime_service.stop(data.task_id)
    return SuccessResponse(data=result)


@router.post("/status", response_model=schemas.TaskRuntimeStatusResponse)
async def task_status(data: schemas.QueryTaskRuntime, db: Session = Depends(get_db)):
    task_runtime_service = TaskRuntimeService(db)
    result = task_runtime_service.status(data.task_id)
    return SuccessResponse(data=result)


@router.post("/runs", response_model=schemas.TaskRunHistoryResponse)
async def task_runs(data: schemas.QueryTaskRuntime, db: Session = Depends(get_db)):
    task_runtime_service = TaskRuntimeService(db)
    result = task_runtime_service.list_runs(data.task_id)
    return SuccessResponse(data=result)


@router.post("/report", response_model=schemas.TaskReportResponse)
async def task_report(data: schemas.QueryTaskReport, db: Session = Depends(get_db)):
    task_runtime_service = TaskRuntimeService(db)
    result = task_runtime_service.report(data.task_id, data.task_run_id)
    return SuccessResponse(data=result)
