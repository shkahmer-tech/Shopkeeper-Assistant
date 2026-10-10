"""
Inventory management service.

Refactor of PART 3 (inventory_check) from the original ML_code.py, plus a
logging addition: every check is appended to data/inventory_log.csv, so
your inventory history accumulates over time — useful later if you want
to train a model on reorder decisions instead of using fixed rules.
"""

from datetime import datetime
from typing import Tuple

import pandas as pd

from app.core.config import settings


def check_inventory(
    current_stock: int, weekly_demand: float, monthly_demand: float
) -> Tuple[int, str, str]:
    """Returns (reorder_units, status, action_note)."""
    if current_stock >= monthly_demand:
        status = "SUFFICIENT for 30 days"
        reorder = 0
        note = "No reorder needed."
    elif current_stock >= weekly_demand:
        reorder = round(monthly_demand - current_stock)
        status = "Covers 1 week only"
        note = f"Order {reorder} units soon."
    else:
        reorder = round(monthly_demand - current_stock)
        status = "CRITICALLY LOW"
        note = f"Urgent: order {reorder} units immediately!"

    return int(max(reorder, 0)), status, note


def log_inventory_check(
    current_stock: int,
    weekly_demand: float,
    monthly_demand: float,
    status: str,
    reorder_units: int,
) -> None:
    """Appends this check to data/inventory_log.csv so every manual entry
    is saved and available later (e.g. for analysis or training a
    reorder-prediction model)."""
    log_path = settings.DATA_DIR / settings.INVENTORY_LOG_CSV
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "current_stock": current_stock,
        "weekly_demand": weekly_demand,
        "monthly_demand": monthly_demand,
        "status": status,
        "reorder_units": reorder_units,
    }
    if log_path.exists():
        existing = pd.read_csv(log_path)
        combined = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
    else:
        combined = pd.DataFrame([row])
    combined.to_csv(log_path, index=False)