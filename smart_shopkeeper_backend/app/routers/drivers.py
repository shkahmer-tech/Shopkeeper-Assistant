"""
Driver roster route.

  GET /api/drivers - view every driver and whether they're available or busy
"""

from fastapi import APIRouter

from app.services import driver_service

router = APIRouter(prefix="/api/drivers", tags=["Drivers"])


@router.get("")
def list_drivers():
    return driver_service.list_drivers()