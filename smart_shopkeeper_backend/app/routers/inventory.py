"""
Inventory management routes (per category).

  GET  /api/inventory/stock     - see the stock of EVERY category + the total
  POST /api/inventory/set-stock - set/restock one category
  POST /api/inventory/sell      - record a sale for one category
  POST /api/inventory/check     - reorder status for one category (or the total)
"""

from datetime import date

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.models.schemas import (
    InventoryCheckRequest,
    InventoryCheckResponse,
    SellUnitsRequest,
    SellUnitsResponse,
    SetStockRequest,
    SetStockResponse,
    StockListResponse,
)
from app.services import category_service, demand_service, inventory_service, stock_service
from app.utils.data_loader import DataLoadError

router = APIRouter(prefix="/api/inventory", tags=["Inventory Management"])


def _require_category(name: str) -> None:
    if name not in category_service.list_categories():
        raise HTTPException(
            status_code=404,
            detail=f"Category '{name}' not found. Add it first with POST /api/categories/add.",
        )


@router.get("/stock", response_model=StockListResponse)
def get_all_stock():
    """Stock of every category (categories with no record show 0)."""
    saved = stock_service.list_stock()
    stock = {name: saved.get(name, 0.0) for name in category_service.list_categories()}
    return StockListResponse(stock=stock, total_stock=sum(stock.values()))


@router.post("/set-stock", response_model=SetStockResponse)
def set_stock(payload: SetStockRequest):
    """Use this once initially, and again any time you physically restock a category."""
    _require_category(payload.category)
    updated = stock_service.set_current_stock(payload.category, payload.current_stock)
    return SetStockResponse(
        category=payload.category,
        current_stock=updated,
        message=f"Stock of '{payload.category}' updated.",
    )


@router.post("/sell", response_model=SellUnitsResponse)
def sell_units(payload: SellUnitsRequest):
    """
    Record a real sale for one category:
    1. Decrements that category's stock.
    2. (Optional, default on) Saves it as demand data and retrains the demand model.
    """
    _require_category(payload.category)
    previous_stock, updated_stock = stock_service.record_sale(payload.category, payload.units_sold)

    demand_record_added = False
    retrained = False
    if payload.add_to_training_data:
        try:
            sale_date = payload.date or str(date.today())
            record = {
                settings.DEMAND_DATE_COL: sale_date,
                settings.DEMAND_TARGET_COL: payload.units_sold,
            }
            if payload.extra_fields:
                record.update(payload.extra_fields)

            rows_in_master, trained = demand_service.add_single_demand_record(
                record, retrain=True
            )
            demand_record_added = True
            retrained = trained is not None
        except DataLoadError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SellUnitsResponse(
        category=payload.category,
        previous_stock=previous_stock,
        units_sold=payload.units_sold,
        updated_stock=updated_stock,
        demand_record_added=demand_record_added,
        retrained=retrained,
        message=f"Sale recorded. '{payload.category}' stock updated from {previous_stock} to {updated_stock}.",
    )


@router.post("/check", response_model=InventoryCheckResponse)
def check_inventory(payload: InventoryCheckRequest):
    """
    Reorder status using the STORED stock (one category, or the total if no
    category is given) and a live demand forecast.
    """
    if payload.category:
        _require_category(payload.category)

    target_date = payload.target_date or str(date.today())

    try:
        _, _, weekly_demand, monthly_demand = demand_service.forecast_demand(target_date)
    except demand_service.ModelNotTrainedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    current_stock = stock_service.get_current_stock(payload.category)

    reorder, status, note = inventory_service.check_inventory(
        current_stock, weekly_demand, monthly_demand
    )

    inventory_service.log_inventory_check(
        current_stock, weekly_demand, monthly_demand, status, reorder
    )

    return InventoryCheckResponse(
        category=payload.category,
        current_stock=current_stock,
        weekly_demand=weekly_demand,
        monthly_demand=monthly_demand,
        status=status,
        reorder_units=reorder,
        action_note=note,
        logged=True,
    )