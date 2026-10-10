"""
Full report route.

  POST /api/report/full - runs the exact same end-to-end flow as main()
  in the original script: forecast demand -> check inventory (+log) ->
  predict delivery -> generate chart -> (optionally) AI review.
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    DeliveryPredictResponse,
    DemandForecastResponse,
    FullReportRequest,
    FullReportResponse,
    InventoryCheckResponse,
)
from app.services import ai_review_service, chart_service, delivery_service, demand_service, inventory_service, stock_service

router = APIRouter(prefix="/api/report", tags=["Full Report"])


@router.post("/full", response_model=FullReportResponse)
def full_report(payload: FullReportRequest):
    # 1. Demand forecast
    try:
        ref_date, daily, weekly, monthly = demand_service.forecast_demand(payload.target_date)
    except demand_service.ModelNotTrainedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    demand_resp = DemandForecastResponse(
        reference_date=ref_date,
        predicted_daily=daily,
        predicted_weekly=weekly,
        predicted_monthly=monthly,
    )

        # 2. Inventory check — uses the STORED current stock (set via
    # /api/inventory/set-stock, maintained by /api/inventory/sell)
    current_stock = stock_service.get_current_stock()
    reorder, status, note = inventory_service.check_inventory(
        current_stock, weekly, monthly
    )
    inventory_service.log_inventory_check(
        current_stock, weekly, monthly, status, reorder
    )
    inventory_resp = InventoryCheckResponse(
        current_stock=current_stock,
        weekly_demand=weekly,
        monthly_demand=monthly,
        status=status,
        reorder_units=reorder,
        action_note=note,
        logged=True,
    )
    
       # 3. Delivery prediction
    try:
        totals = delivery_service.summarize_items(payload.items)
        minutes = delivery_service.predict_delivery_time(
            payload.distance_km, payload.traffic_level,
            totals["total_items"], totals["total_price"],
        )
    except delivery_service.ModelNotTrainedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    delivery_resp = DeliveryPredictResponse(
        distance_km=payload.distance_km,
        traffic_level=payload.traffic_level,
        estimated_minutes=minutes,
        **totals,
    )

    # 4. Chart (best-effort — don't fail the whole report if charting breaks)
    chart_path = None
    try:
        chart_path = chart_service.generate_demand_chart(daily, weekly, monthly)
    except chart_service.ChartDataUnavailableError:
        chart_path = None

    # 5. AI review (optional, best-effort)
    ai_review_text = None
    if payload.include_ai_review:
        try:
            ai_review_text = ai_review_service.generate_ai_review(
                demand_resp, inventory_resp, delivery_resp
            )
        except ai_review_service.AIReviewError:
            ai_review_text = None

    return FullReportResponse(
        demand=demand_resp,
        inventory=inventory_resp,
        delivery=delivery_resp,
        chart_path=chart_path,
        ai_review=ai_review_text,
    )