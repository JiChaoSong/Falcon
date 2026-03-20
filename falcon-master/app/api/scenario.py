# falcon_shared/api/v1/scenario.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.response import SuccessResponse
from app.db import get_db
from app.schemas import scenario as schemas
from app.services.scenario_service import ScenarioService

router = APIRouter(prefix="/scenario", tags=["Scenario"])


@router.post("/list", response_model=schemas.ScenarioListResponse)
async def scenario_list(data:schemas.QueryScenarioList, db: Session = Depends(get_db),):


    scenario_service = ScenarioService(db)

    scenarios = scenario_service.list(**data.model_dump(mode="json"))

    return SuccessResponse(data=scenarios)

@router.post("/info", response_model=schemas.ScenarioInfoResponse)
async def scenario_info(data: schemas.QueryScenarioOne, db: Session = Depends(get_db),):

    scenario_service = ScenarioService(db)

    scenarios = scenario_service.get(**data.model_dump())

    return SuccessResponse(data=scenarios)


@router.post("/delete", response_model=schemas.BaseResponse)
async def scenario_delete(data: schemas.QueryScenarioOne, db: Session = Depends(get_db)):

    scenario_service = ScenarioService(db)

    scenario_service.delete(**data.model_dump())

    return SuccessResponse(data=None)

@router.post("/create", response_model=schemas.ScenarioInfoResponse)
async def scenario_create(data: schemas.ScenarioCreate, db: Session = Depends(get_db)):

    scenario_service = ScenarioService(db)

    scenarios = scenario_service.create(data)

    return SuccessResponse(data=scenarios)

@router.post("/update", response_model=schemas.ScenarioInfoResponse)
async def scenario_update(data: schemas.ScenarioUpdate, db: Session = Depends(get_db)):

    scenario_service = ScenarioService(db)

    scenarios = scenario_service.update(data)

    return SuccessResponse(data=scenarios)
