"""
Driver roster service.

Keeps a small pool of drivers persisted to data/drivers.json, each with an
availability status ("available" / "busy"). order_service.py pulls an
available driver when an order is confirmed, and frees them again once the
order is delivered or cancelled.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import settings

DEFAULT_DRIVERS: List[Dict] = [
    {"driver_id": "DRV-001", "name": "Ali Raza", "phone": "+92-300-1111111", "vehicle_type": "Bike", "status": "available", "max_items": 15, "max_weight_kg": 10.0},
    {"driver_id": "DRV-002", "name": "Usman Tariq", "phone": "+92-300-2222222", "vehicle_type": "Bike", "status": "available", "max_items": 15, "max_weight_kg": 10.0},
    {"driver_id": "DRV-003", "name": "Bilal Ahmed", "phone": "+92-300-3333333", "vehicle_type": "Car", "status": "available", "max_items": 60, "max_weight_kg": 80.0},
]


def _drivers_path() -> Path:
    return settings.DATA_DIR / "drivers.json"


def _load_drivers() -> List[Dict]:
    path = _drivers_path()
    if not path.exists():
        _save_drivers(DEFAULT_DRIVERS)
        return [d.copy() for d in DEFAULT_DRIVERS]
    with open(path, "r") as f:
        return json.load(f)


def _save_drivers(drivers: List[Dict]) -> None:
    path = _drivers_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(drivers, f, indent=2)


def list_drivers() -> List[Dict]:
    return _load_drivers()


def can_carry(driver: Dict, total_items: int, total_weight_kg: float) -> bool:
    """True if this driver's vehicle can hold the whole delivery.
    Older drivers.json entries without limits fall back to generous defaults."""
    return (
        total_items <= driver.get("max_items", 20)
        and total_weight_kg <= driver.get("max_weight_kg", 15.0)
    )


def get_available_driver(total_items: int = 0, total_weight_kg: float = 0.0) -> Optional[Dict]:
    """Returns an AVAILABLE driver whose vehicle can carry the load
    (smallest suitable vehicle first, so cars stay free for big orders)."""
    candidates = [
        d for d in _load_drivers()
        if d["status"] == "available" and can_carry(d, total_items, total_weight_kg)
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda d: (d.get("max_weight_kg", 15.0), d.get("max_items", 20)))


def any_driver_can_carry(total_items: int, total_weight_kg: float) -> bool:
    """Used to tell 'all riders busy' apart from 'order too big for every vehicle'."""
    return any(can_carry(d, total_items, total_weight_kg) for d in _load_drivers())


def set_driver_status(driver_id: str, status: str) -> Optional[Dict]:
    drivers = _load_drivers()
    updated = None
    for d in drivers:
        if d["driver_id"] == driver_id:
            d["status"] = status
            updated = d
            break
    if updated is not None:
        _save_drivers(drivers)
    return updated