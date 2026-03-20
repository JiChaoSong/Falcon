from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import SuccessResponse
from app.db import get_db
from app.schemas.dashboard import DashboardOverviewResponse
from app.services.dashboard_service import DashboardService


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
async def dashboard_overview(db: Session = Depends(get_db)):
    dashboard_service = DashboardService(db)
    result = dashboard_service.overview()
    return SuccessResponse(data=result)
