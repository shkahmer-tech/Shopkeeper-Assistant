"""
Health check route — confirms the API is up and tells you at a glance
whether the demand and delivery models have been trained yet.
"""

from fastapi import APIRouter

from app.models.schemas import HealthResponse
from app.services.model_store import model_store

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
def health_check():
    status = model_store.status()
    return HealthResponse(status="ok", **status)
