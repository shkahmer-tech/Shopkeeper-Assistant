"""
Per-category stock tracking.
Stock is stored per category in data/category_stock.json, e.g.
{"Milk": {"current_stock": 42.0, "updated_at": "..."}}
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from app.core.config import settings


def _stock_path() -> Path:
    return settings.DATA_DIR / "category_stock.json"


def _load() -> Dict[str, dict]:
    path = _stock_path()
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save(data: Dict[str, dict]) -> None:
    path = _stock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def list_stock() -> Dict[str, float]:
    """{category: stock} for every category that has a stock record."""
    return {name: float(v["current_stock"]) for name, v in _load().items()}


def get_current_stock(category: Optional[str] = None) -> float:
    """Stock of one category, or the TOTAL across all categories if category is None."""
    stock = list_stock()
    if category is None:
        return sum(stock.values())
    return stock.get(category, 0.0)


def set_current_stock(category: str, value: float) -> float:
    """Set/overwrite one category's stock (initial value or restock)."""
    data = _load()
    data[category] = {"current_stock": float(value), "updated_at": datetime.utcnow().isoformat()}
    _save(data)
    return float(value)


def record_sale(category: str, units_sold: float) -> Tuple[float, float]:
    """Decrements one category's stock (never below 0). Returns (previous, updated)."""
    previous = get_current_stock(category)
    updated = max(0.0, previous - units_sold)
    set_current_stock(category, updated)
    return previous, updated


def remove_category_stock(category: str) -> None:
    data = _load()
    data.pop(category, None)
    _save(data)