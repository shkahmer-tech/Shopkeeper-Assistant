"""
Order & delivery-tracking service.

This is the "confirm order" flow you'd see in a food-delivery app:
  1. create_order() predicts the ETA, assigns a free driver, and issues a
     tracking ID.
  2. update_order_status() moves the order through Picked Up -> On the
     Way -> Delivered (or Cancelled), freeing the driver at the end.
  3. If the order is marked Delivered with a real actual_minutes value,
     that becomes a genuine training data point fed back into the
     delivery model — same pattern as add_single_delivery_record.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from app.core.config import settings
from app.services import delivery_service, driver_service

VALID_STATUSES = ["Driver Assigned", "Picked Up", "On the Way", "Delivered", "Cancelled"]


class NoDriversAvailableError(Exception):
    """Raised when every driver in the roster is currently busy."""
class OrderTooLargeError(Exception):
    """Raised when no vehicle in the roster can carry the order's items."""

def _orders_path() -> Path:
    return settings.DATA_DIR / "orders.json"


def _load_orders() -> Dict[str, dict]:
    path = _orders_path()
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save_orders(orders: Dict[str, dict]) -> None:
    path = _orders_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(orders, f, indent=2)


def _compute_remaining_minutes(order: dict) -> float:
    """
    Live countdown: estimated_minutes minus however much real time has
    passed since the order was created. Locks to 0 once the order is
    Delivered or Cancelled — the trip is over, there's nothing left to wait for.
    """
    if order["status"] in ("Delivered", "Cancelled"):
        return 0.0
    created = datetime.fromisoformat(order["created_at"])
    elapsed_minutes = (datetime.utcnow() - created).total_seconds() / 60.0
    remaining = order["estimated_minutes"] - elapsed_minutes
    return round(max(0.0, remaining), 1)


def _attach_remaining(order: dict) -> dict:
    """
    Returns a COPY of the order with remaining_minutes computed fresh.
    We never save remaining_minutes to disk — it's recalculated every
    time an order is read, so it's always accurate to "right now."
    """
    order_with_remaining = dict(order)
    order_with_remaining["remaining_minutes"] = _compute_remaining_minutes(order)

    # Item totals (older saved orders without items still work)
    items = order.get("items", [])
    order_with_remaining["items"] = items
    order_with_remaining.setdefault("total_items", 0)
    order_with_remaining["items_delivered"] = sum(i["quantity"] for i in items if i.get("delivered"))
    order_with_remaining["items_remaining"] = sum(i["quantity"] for i in items if not i.get("delivered"))
    return order_with_remaining


def create_order(
    distance_km: float,
    traffic_level: float,
    items: Optional[list] = None,
    extra_fields: Optional[dict] = None,
) -> dict:
    """
    Confirms a new order: totals the items, predicts delivery time (distance +
    traffic + item load), assigns an available driver whose vehicle can carry
    the items, and generates a tracking ID.
    """
    item_dicts = [(i if isinstance(i, dict) else i.dict()) for i in (items or [])]
    for i in item_dicts:
        i["delivered"] = False
    totals = delivery_service.summarize_items(item_dicts)

    estimated_minutes = delivery_service.predict_delivery_time(
        distance_km, traffic_level, totals["total_items"], totals["total_price"]
    )

    if not driver_service.any_driver_can_carry(totals["total_items"], totals["total_weight_kg"]):
        raise OrderTooLargeError(
            f"This order ({totals['total_items']} items, {totals['total_weight_kg']} kg) "
            "is too large for every vehicle. Split it into smaller orders."
        )

    driver = driver_service.get_available_driver(totals["total_items"], totals["total_weight_kg"])
    if driver is None:
        raise NoDriversAvailableError(
            "No driver who can carry this order is currently available. Try again shortly."
        )
    

    driver_service.set_driver_status(driver["driver_id"], "busy")

    tracking_id = "ORD-" + uuid.uuid4().hex[:8].upper()
    now = datetime.utcnow().isoformat()
    order = {
        "tracking_id": tracking_id,
        "status": "Driver Assigned",
        "distance_km": distance_km,
        "traffic_level": traffic_level,
        "items": item_dicts,
        **totals,
        "estimated_minutes": estimated_minutes,
        "driver": driver,
        "extra_fields": extra_fields or {},
        "created_at": now,
        "updated_at": now,
        "actual_minutes": None,
    }

    orders = _load_orders()
    orders[tracking_id] = order
    _save_orders(orders)
    return _attach_remaining(order)


def get_order(tracking_id: str) -> Optional[dict]:
    order = _load_orders().get(tracking_id)
    return _attach_remaining(order) if order else None


def list_orders() -> Dict[str, dict]:
    return {tid: _attach_remaining(o) for tid, o in _load_orders().items()}


def update_order_status(
    tracking_id: str,
    new_status: str,
    actual_minutes: Optional[float] = None,
    delivered_items: Optional[list] = None,
) -> Optional[dict]:
    """
    Moves an order to a new status. On Delivered or Cancelled, the
    assigned driver is freed up again. On Delivered with a real
    actual_minutes value, that becomes a genuine training data point
    fed back into the delivery model.
    """
    orders = _load_orders()
    order = orders.get(tracking_id)
    if order is None:
        return None

    order["status"] = new_status
    order["updated_at"] = datetime.utcnow().isoformat()

    # Per-item tracking: mark named items as handed over; Delivered = everything handed over
    if delivered_items:
        wanted = {n.strip().lower() for n in delivered_items}
        for it in order.get("items", []):
            if it["name"].strip().lower() in wanted:
                it["delivered"] = True
    if new_status == "Delivered":
        for it in order.get("items", []):
            it["delivered"] = True

    if new_status in ("Delivered", "Cancelled"):
        driver_service.set_driver_status(order["driver"]["driver_id"], "available")

        if new_status == "Delivered" and actual_minutes is not None:
            record = {
                settings.DELIVERY_DIST_COL: order["distance_km"],
                settings.DELIVERY_TRAFFIC_COL: order["traffic_level"],
                settings.DELIVERY_TARGET_COL: actual_minutes,
                "Quantity": order.get("total_items", 0),
                "Total_Price": order.get("total_price", 0.0),
            }
            record.update(order.get("extra_fields") or {})
            try:
                delivery_service.add_single_delivery_record(record, retrain=True)
                order["actual_minutes"] = actual_minutes
            except Exception:
                pass  # order status still updates even if retraining fails

    orders[tracking_id] = order
    _save_orders(orders)
    return _attach_remaining(order)