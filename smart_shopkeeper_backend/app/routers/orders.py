"""
Order & delivery tracking routes — like a food-delivery app's order flow.

  POST /api/orders/create              - confirm an order: predicts ETA, assigns a driver, issues a tracking ID
  GET  /api/orders/{tracking_id}       - track an order (driver details + status + ETA)
  POST /api/orders/{tracking_id}/status - move the order forward (Picked Up / On the Way / Delivered / Cancelled)
  GET  /api/orders                      - list all orders (for testing/admin)
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import CreateOrderRequest, OrderResponse, UpdateOrderStatusRequest
from app.services import delivery_service, order_service

router = APIRouter(prefix="/api/orders", tags=["Orders & Delivery Tracking"])


@router.post("/create", response_model=OrderResponse)
def create_order(payload: CreateOrderRequest):
    try:
        order = order_service.create_order(
            payload.distance_km, payload.traffic_level, payload.items, payload.extra_fields
        )
        return order
    except delivery_service.ModelNotTrainedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except order_service.OrderTooLargeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except order_service.NoDriversAvailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{tracking_id}", response_model=OrderResponse)
def track_order(tracking_id: str):
    order = order_service.get_order(tracking_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Tracking ID not found.")
    return order


@router.post("/{tracking_id}/status", response_model=OrderResponse)
def update_status(tracking_id: str, payload: UpdateOrderStatusRequest):
    if payload.status not in order_service.VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {order_service.VALID_STATUSES}",
        )
    order = order_service.update_order_status(
        tracking_id, payload.status, payload.actual_minutes, payload.delivered_items
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Tracking ID not found.")
    return order


@router.get("")
def list_all_orders():
    return order_service.list_orders()