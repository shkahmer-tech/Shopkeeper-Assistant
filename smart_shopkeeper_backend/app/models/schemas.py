"""
Pydantic schemas — the request/response "contracts" for every route.
Keeping these separate from the services means the API shape can evolve
without touching the ML logic, and vice versa.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Demand ──────────────────────────────────────────────────────────
class DemandTrainResponse(BaseModel):
    rows_used: int
    features_used: List[str]
    mae: float
    r2_score: float
    message: str


class DemandForecastRequest(BaseModel):
    target_date: str = Field(..., example="2024-06-15")


class DemandForecastResponse(BaseModel):
    reference_date: str
    predicted_daily: float
    predicted_weekly: float
    predicted_monthly: float


class AddDemandRecordRequest(BaseModel):
    """
    Submit ONE real, actual data point (not a prediction) to grow the
    dataset — e.g. what you actually sold on a given day. Keys in
    `record` must match your CSV's column names, e.g.:
    {"Date": "2024-06-15", "Product ID": "P1", "Units Sold": 42, "Category": "A"}
    """
    record: Dict[str, Any] = Field(..., example={
        "Date": "2024-06-15", "Product ID": "P1", "Units Sold": 42, "Category": "A"
    })
    retrain: bool = Field(True, description="If true, retrains the model immediately on the updated dataset.")


class AddRecordResponse(BaseModel):
    rows_in_master: int
    retrained: bool
    mae: Optional[float] = None
    r2_score: Optional[float] = None
    message: str


class InventoryCheckRequest(BaseModel):
    target_date: Optional[str] = Field(
        None,
        example="2024-06-15",
        description="Date to forecast demand for. Defaults to today if omitted.",
    )
    category: Optional[str] = Field(
        None, example="Milk",
        description="Check one category. If omitted, uses the TOTAL stock of all categories.",
    )


class InventoryCheckResponse(BaseModel):
    category: Optional[str] = None
    current_stock: float
    weekly_demand: float
    monthly_demand: float
    status: str
    reorder_units: int
    action_note: str
    logged: bool = True


class SetStockRequest(BaseModel):
    category: str = Field(..., example="Milk", description="Must already exist in /api/categories.")
    current_stock: float = Field(..., ge=0, example=200, description="Sets/overwrites this category's stock — use for initial setup or after a restock.")


class SetStockResponse(BaseModel):
    category: str
    current_stock: float
    message: str


class SellUnitsRequest(BaseModel):
    category: str = Field(..., example="Milk", description="Must already exist in /api/categories.")
    units_sold: float = Field(..., gt=0, example=5)
    date: Optional[str] = Field(
        None, example="2024-06-20",
        description="Date of the sale. Defaults to today if omitted."
    )
    extra_fields: Optional[Dict[str, Any]] = Field(
        None,
        example={"Product ID": "P1", "Category": "A"},
        description="Any other columns your demand CSV has (matching its column names). Only used if add_to_training_data is true.",
    )
    add_to_training_data: bool = Field(
        True,
        description="If true, this sale is also saved as a real demand record and the model retrains immediately.",
    )


class SellUnitsResponse(BaseModel):
    category: str
    previous_stock: float
    units_sold: float
    updated_stock: float
    demand_record_added: bool
    retrained: bool
    message: str


class StockListResponse(BaseModel):
    stock: Dict[str, float]
    total_stock: float


# ── Delivery ────────────────────────────────────────────────────────
class DeliveryTrainResponse(BaseModel):
    rows_used: int
    features_used: List[str]
    mae_minutes: float
    r2_score: float
    message: str


class OrderItem(BaseModel):
    """One product inside a delivery (what the rider actually carries)."""
    name: str = Field(..., example="Milk 1L")
    quantity: int = Field(..., ge=1, example=2)
    unit_price: float = Field(0.0, ge=0, example=150.0)
    unit_weight_kg: float = Field(0.0, ge=0, example=1.0, description="Weight of ONE unit in kg.")


class DeliveryPredictRequest(BaseModel):
    distance_km: float = Field(..., ge=0, example=10.0)
    traffic_level: float = Field(..., ge=0, example=5.0)
    items: Optional[List[OrderItem]] = Field(
        None, description="Optional. Items being delivered; used as extra model inputs (Quantity, Total_Price)."
    )


class DeliveryPredictResponse(BaseModel):
    distance_km: float
    traffic_level: float
    estimated_minutes: float
    total_items: int = 0
    total_weight_kg: float = 0.0
    total_price: float = 0.0


class AddDeliveryRecordRequest(BaseModel):
    """
    Submit ONE real, actual delivery record to grow the dataset — e.g. an
    order that actually happened, with its real delivery duration. Keys in
    `record` must match your CSV's column names, e.g.:
    {"Delivery_Distance_km": 10, "Traffic_Level": 5, "Quantity": 3,
     "Total_Price": 120, "Driver_Availability": 1, "Delivery_Duration_Minutes": 32}
    """
    record: Dict[str, Any] = Field(..., example={
        "Delivery_Distance_km": 10, "Traffic_Level": 5, "Quantity": 3,
        "Total_Price": 120, "Driver_Availability": 1, "Delivery_Duration_Minutes": 32
    })
    retrain: bool = Field(True, description="If true, retrains the model immediately on the updated dataset.")

# ── Orders & Driver Tracking ─────────────────────────────────────────
class DriverInfo(BaseModel):
    driver_id: str
    name: str
    phone: str
    vehicle_type: str
    status: str
    max_items: int = 20
    max_weight_kg: float = 15.0


class CreateOrderRequest(BaseModel):
    distance_km: float = Field(..., ge=0, example=10.0)
    traffic_level: float = Field(..., ge=0, example=5.0)
    items: List[OrderItem] = Field(
        default_factory=list,
        description="Items in this delivery. The assigned rider must be able to carry them (max_items / max_weight_kg).",
    )
    extra_fields: Optional[Dict[str, Any]] = Field(
        None,
        example={"Quantity": 2, "Total_Price": 45.0},
        description="Any extra columns your delivery CSV has. Stored with the order and reused if you later feed the real outcome back into training.",
    )


class OrderItemStatus(OrderItem):
    delivered: bool = False


class OrderResponse(BaseModel):
    tracking_id: str
    status: str
    distance_km: float
    traffic_level: float
    items: List[OrderItemStatus] = []
    total_items: int = 0
    total_weight_kg: float = 0.0
    total_price: float = 0.0
    items_delivered: int = 0
    items_remaining: int = 0
    estimated_minutes: float
    remaining_minutes: float
    driver: DriverInfo
    created_at: str
    updated_at: str
    actual_minutes: Optional[float] = None


class UpdateOrderStatusRequest(BaseModel):
    status: str = Field(
        ..., example="Delivered",
        description="One of: Driver Assigned, Picked Up, On the Way, Delivered, Cancelled",
    )
    actual_minutes: Optional[float] = Field(
        None,
        description="If status is Delivered, optionally provide the REAL delivery time so the model learns from it.",
    )
    delivered_items: Optional[List[str]] = Field(
        None,
        example=["Milk 1L"],
        description="Names of items handed over so far (partial delivery tracking). On status Delivered, all items are marked delivered.",
    )
# ── Charts ──────────────────────────────────────────────────────────
class ChartResponse(BaseModel):
    chart_path: str
    message: str


# ── Full report (combines everything) ────────────────────────────────
class FullReportRequest(BaseModel):
    target_date: str = Field(..., example="2024-06-15")
    distance_km: float = Field(..., ge=0, example=10.0)
    traffic_level: float = Field(..., ge=0, example=5.0)
    items: Optional[List[OrderItem]] = None 
    include_ai_review: bool = True


class FullReportResponse(BaseModel):
    demand: DemandForecastResponse
    inventory: InventoryCheckResponse
    delivery: DeliveryPredictResponse
    chart_path: Optional[str] = None
    ai_review: Optional[str] = None


# ── AI Review ───────────────────────────────────────────────────────
class AIReviewRequest(BaseModel):
    demand: DemandForecastResponse
    inventory: InventoryCheckResponse
    delivery: DeliveryPredictResponse


class AIReviewResponse(BaseModel):
    review: str

# ── Categories ──────────────────────────────────────────────────────
class CategoryRequest(BaseModel):
    name: str = Field(..., example="Milk", description="The category/product name to add.")
    initial_stock: float = Field(
        0.0, ge=0, example=50,
        description="How many units you're starting with. Optional — defaults to 0, and you can restock later.",
    )


class CategoryRemoveRequest(BaseModel):
    name: str = Field(..., example="Milk")


class CategoryListResponse(BaseModel):
    categories: List[str]
    message: Optional[str] = None

# ── Health ──────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    demand_model_trained: bool
    delivery_model_trained: bool