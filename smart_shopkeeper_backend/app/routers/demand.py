"""
Demand forecasting routes.

  POST /api/demand/train       - (re)train on the configured/uploaded CSV (bulk, cumulative)
  POST /api/demand/forecast    - get daily/weekly/monthly forecast for a date
  POST /api/demand/add-record  - add ONE real data point and optionally retrain
"""

import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import (
    AddDemandRecordRequest,
    AddRecordResponse,
    DemandForecastRequest,
    DemandForecastResponse,
    DemandTrainResponse,
)
from app.services import demand_service
from app.utils.data_loader import DataLoadError

router = APIRouter(prefix="/api/demand", tags=["Demand Forecasting"])


@router.post("/train", response_model=DemandTrainResponse)
async def train_demand(file: Optional[UploadFile] = File(default=None)):
    """
    Train the demand forecasting model.
    - If no file is uploaded, uses the master dataset (seeded from
      DEMAND_CSV in /data on first run).
    - If a CSV is uploaded, its rows are merged into the master dataset
      and training runs on the full accumulated history.
    """
    tmp_path = None
    try:
        if file is not None:
            suffix = Path(file.filename).suffix or ".csv"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = Path(tmp.name)

        trained = demand_service.train_demand_model(tmp_path)
        return DemandTrainResponse(
            rows_used=trained.rows_used,
            features_used=trained.feature_cols,
            mae=trained.mae,
            r2_score=trained.r2,
            message="Demand model trained successfully.",
        )
    except DataLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


@router.post("/forecast", response_model=DemandForecastResponse)
def forecast_demand(payload: DemandForecastRequest):
    try:
        ref_date, daily, weekly, monthly = demand_service.forecast_demand(payload.target_date)
        return DemandForecastResponse(
            reference_date=ref_date,
            predicted_daily=daily,
            predicted_weekly=weekly,
            predicted_monthly=monthly,
        )
    except demand_service.ModelNotTrainedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/add-record", response_model=AddRecordResponse)
def add_demand_record(payload: AddDemandRecordRequest):
    """
    Add ONE real, manually entered demand data point (e.g. what you
    actually sold today) and optionally retrain immediately so the model
    reflects it right away.
    """
    try:
        rows_in_master, trained = demand_service.add_single_demand_record(
            payload.record, payload.retrain
        )
        return AddRecordResponse(
            rows_in_master=rows_in_master,
            retrained=trained is not None,
            mae=trained.mae if trained else None,
            r2_score=trained.r2 if trained else None,
            message=(
                "Record added and model retrained."
                if trained
                else "Record added and saved. Retrain later via /api/demand/train."
            ),
        )
    except DataLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc