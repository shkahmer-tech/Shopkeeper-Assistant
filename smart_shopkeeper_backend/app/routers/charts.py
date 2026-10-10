"""
Chart routes.

  POST /api/charts/generate      - generate the analytics chart, returns its path
  GET  /api/charts/{filename}    - download/view a previously generated chart
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings
from app.models.schemas import ChartResponse, DemandForecastRequest
from app.services import chart_service, demand_service

router = APIRouter(prefix="/api/charts", tags=["Charts"])


@router.post("/generate", response_model=ChartResponse)
def generate_chart(payload: DemandForecastRequest):
    try:
        _, daily, weekly, monthly = demand_service.forecast_demand(payload.target_date)
        path = chart_service.generate_demand_chart(daily, weekly, monthly)
        return ChartResponse(chart_path=path, message="Chart generated successfully.")
    except demand_service.ModelNotTrainedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except chart_service.ChartDataUnavailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{filename}")
def get_chart(filename: str):
    path = settings.CHARTS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Chart not found.")
    return FileResponse(path, media_type="image/png")
