"""
Delivery time prediction routes.

  POST /api/delivery/train       - (re)train on the configured/uploaded CSV (bulk, cumulative)
  POST /api/delivery/predict     - predict delivery time for a distance/traffic pair
  POST /api/delivery/add-record  - add ONE real delivery record and optionally retrain
"""

import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import (
    AddDeliveryRecordRequest,
    AddRecordResponse,
    DeliveryPredictRequest,
    DeliveryPredictResponse,
    DeliveryTrainResponse,
)
from app.services import delivery_service
from app.utils.data_loader import DataLoadError

router = APIRouter(prefix="/api/delivery", tags=["Delivery Prediction"])


@router.post("/train", response_model=DeliveryTrainResponse)
async def train_delivery(file: Optional[UploadFile] = File(default=None)):
    tmp_path = None
    try:
        if file is not None:
            suffix = Path(file.filename).suffix or ".csv"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = Path(tmp.name)

        trained = delivery_service.train_delivery_model(tmp_path)
        return DeliveryTrainResponse(
            rows_used=trained.rows_used,
            features_used=trained.feature_cols,
            mae_minutes=trained.mae,
            r2_score=trained.r2,
            message="Delivery model trained successfully.",
        )
    except DataLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


@router.post("/predict", response_model=DeliveryPredictResponse)
def predict_delivery(payload: DeliveryPredictRequest):
    try:
        totals = delivery_service.summarize_items(payload.items)
        minutes = delivery_service.predict_delivery_time(
            payload.distance_km, payload.traffic_level,
            totals["total_items"], totals["total_price"],
        )
        return DeliveryPredictResponse(
            distance_km=payload.distance_km,
            traffic_level=payload.traffic_level,
            estimated_minutes=minutes,
            **totals,
        )
    except delivery_service.ModelNotTrainedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/add-record", response_model=AddRecordResponse)
def add_delivery_record(payload: AddDeliveryRecordRequest):
    """
    Add ONE real, manually entered delivery record (e.g. an order that
    actually happened, with its real duration) and optionally retrain
    immediately.
    """
    try:
        rows_in_master, trained = delivery_service.add_single_delivery_record(
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
                else "Record added and saved. Retrain later via /api/delivery/train."
            ),
        )
    except DataLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc