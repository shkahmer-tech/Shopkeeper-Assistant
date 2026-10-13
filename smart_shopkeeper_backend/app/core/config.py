"""
Central configuration for the Smart Shopkeeper Assistant backend.

Everything that used to sit in the hardcoded "CONFIG" block at the top of
ML_code.py now lives here, as environment-overridable settings. This is the
one place you change column names / defaults instead of editing model code.
"""

from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # ── App ─────────────────────────────────────────────────────────
    APP_NAME: str = "Smart Shopkeeper Assistant API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ── Server (change PORT here, or override via .env / env var) ───
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    CORS_ORIGINS: List[str] = ["*"]
    # ── File locations ─────────────────────────────────────────────
    DATA_DIR: Path = BASE_DIR / "data"
    CHARTS_DIR: Path = BASE_DIR / "outputs" / "charts"
    MODELS_DIR: Path = BASE_DIR / "outputs" / "models"

    DEMAND_CSV: str = "retail_store_inventory.csv"
    DELIVERY_CSV: str = "talabat_enhanced_orders.csv"

    # ── Cumulative "master" datasets (grow every time you train with new data) ──
    DEMAND_MASTER_CSV: str = "demand_master.csv"
    DELIVERY_MASTER_CSV: str = "delivery_master.csv"

    # ── Inventory check log (grows every time /api/inventory/check is called) ──
    INVENTORY_LOG_CSV: str = "inventory_log.csv"

    # ── Demand dataset column mapping ─────────────────────────────
    DEMAND_DATE_COL: str = "Date"
    DEMAND_TARGET_COL: str = "Units Sold"
    DEMAND_PRODUCT_COL: str = "Product ID"

    # ── Delivery dataset column mapping ───────────────────────────
    DELIVERY_DIST_COL: str = "Delivery_Distance_km"
    DELIVERY_TRAFFIC_COL: str = "Traffic_Level"
    DELIVERY_TARGET_COL: str = "Delivery_Duration_Minutes"
    DELIVERY_WEATHER_COL: Optional[str] = None
    DELIVERY_EXTRA_FEATURES: List[str] = [
        "Quantity",
        "Total_Price",
        "Driver_Availability",
    ]

    # ── AI Review (Google Gemini API) ──────────────────────────────
    GEMINI_API_KEY: Optional[str] = None
    AI_REVIEW_MODEL: str = "gemini-3.6-flash"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Make sure runtime directories exist on import
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CHARTS_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)