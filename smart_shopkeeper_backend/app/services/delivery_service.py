"""
Delivery time prediction service.

Refactor of the delivery half of PART 4 from the original ML_code.py.
Trains a RandomForestRegressor on distance, traffic and any configured
extra numeric features to predict delivery duration in minutes.

Two ways to grow the training data over time:
  - train_delivery_model(): bulk CSV upload, merged into the master dataset.
  - add_single_delivery_record(): one manually entered real data point,
    appended to the master dataset and optionally retrained immediately.
"""

from pathlib import Path
from typing import Optional

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from app.core.config import settings
from app.services.model_store import TrainedModel, model_store
from app.utils.data_loader import load_delivery_df, merge_into_master, append_single_record


class ModelNotTrainedError(Exception):
    """Raised when a prediction is requested before the model is trained."""


def train_delivery_model(file_path: Optional[Path] = None) -> TrainedModel:
    """
    Same cumulative pattern as demand: new uploads are appended to
    data/delivery_master.csv, and training always runs on the full
    accumulated dataset.
    """
    default_path = settings.DATA_DIR / settings.DELIVERY_CSV
    master_path = settings.DATA_DIR / settings.DELIVERY_MASTER_CSV
    training_path = merge_into_master(file_path, master_path, default_path)
    return _train_on_path(training_path)


def _train_on_path(training_path: Path) -> TrainedModel:
    """Core training logic on an already-resolved CSV path (no merging).
    Shared by train_delivery_model() and add_single_delivery_record()."""
    df = load_delivery_df(training_path)

    feature_cols = [c for c in df.columns if c != settings.DELIVERY_TARGET_COL]
    X = df[feature_cols].fillna(df[feature_cols].median())
    y = df[settings.DELIVERY_TARGET_COL]

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=150, random_state=42, n_jobs=-1)
    model.fit(X_tr, y_tr)

    y_pred = model.predict(X_te)
    trained = TrainedModel(
        model=model,
        feature_cols=feature_cols,
        mae=round(float(mean_absolute_error(y_te, y_pred)), 2),
        r2=round(float(r2_score(y_te, y_pred)), 4),
        rows_used=len(df),
    )
    model_store.set_delivery(trained)
    return trained

def summarize_items(items) -> dict:
    """items: list of dicts or OrderItem objects -> totals used by the model & API."""
    total_items, total_weight, total_price = 0, 0.0, 0.0
    for it in items or []:
        d = it if isinstance(it, dict) else it.dict()
        q = int(d.get("quantity", 0))
        total_items += q
        total_weight += q * float(d.get("unit_weight_kg", 0.0))
        total_price += q * float(d.get("unit_price", 0.0))
    return {
        "total_items": total_items,
        "total_weight_kg": round(total_weight, 2),
        "total_price": round(total_price, 2),
    }


def predict_delivery_time(
    distance_km: float,
    traffic_level: float,
    total_items: int = 0,
    total_price: float = 0.0,
) -> float:
    trained = model_store.get_delivery()
    if trained is None:
        raise ModelNotTrainedError(
            "Delivery model has not been trained yet. Call /api/delivery/train first."
        )

    row = {}
    for fc in trained.feature_cols:
        fcl = fc.lower()
        if "distance" in fcl or "dist" in fcl or "km" in fcl:
            row[fc] = distance_km
        elif "traffic" in fcl:
            row[fc] = traffic_level
        elif "quantity" in fcl:
            row[fc] = total_items
        elif "price" in fcl:
            row[fc] = total_price
        elif "weather" in fcl:
            row[fc] = 0
        else:
            row[fc] = 0

    df_row = pd.DataFrame([row])[trained.feature_cols]
    return round(max(0.0, float(trained.model.predict(df_row)[0])), 1)


def add_single_delivery_record(record: dict, retrain: bool = True):
    """
    Appends ONE real, manually entered delivery record to the master
    dataset (e.g. an order that actually happened, with its real
    duration). If retrain=True, retrains immediately; otherwise it's
    just saved for the next training run.

    Returns (rows_in_master, trained_or_none).
    """
    default_path = settings.DATA_DIR / settings.DELIVERY_CSV
    master_path = settings.DATA_DIR / settings.DELIVERY_MASTER_CSV
    append_single_record(record, master_path, default_path)

    rows_in_master = len(pd.read_csv(master_path))

    trained = None
    if retrain:
        trained = _train_on_path(master_path)

    return rows_in_master, trained