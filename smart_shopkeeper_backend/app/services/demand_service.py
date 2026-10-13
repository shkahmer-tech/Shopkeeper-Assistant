"""
Demand forecasting service.

Refactor of PART 2 (train_demand_model / forecast_demands) from the
original ML_code.py. Trains a RandomForestRegressor on time features
(+ any other numeric columns in the dataset) to predict units sold,
then rolls that up into daily / weekly / monthly forecasts.

Two ways to grow the training data over time:
  - train_demand_model(): bulk CSV upload, merged into the master dataset.
  - add_single_demand_record(): one manually entered real data point,
    appended to the master dataset and optionally retrained immediately.
"""

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from app.core.config import settings
from app.services.model_store import TrainedModel, model_store
from app.utils.data_loader import (
    load_demand_df,
    merge_into_master,
    append_single_record,
    DataLoadError,
)


TIME_FEATURES = ["day", "week", "month", "year", "dayofweek", "dayofyear"]


class ModelNotTrainedError(Exception):
    """Raised when a forecast is requested before the model is trained."""


def train_demand_model(file_path: Optional[Path] = None) -> TrainedModel:
    """
    Loads data, trains the RF regressor, and caches + persists it.

    If `file_path` is a newly uploaded CSV, its rows are appended to the
    cumulative master dataset (data/demand_master.csv) before training, so
    every training call incorporates all data given so far — not just the
    latest upload.
    """
    default_path = settings.DATA_DIR / settings.DEMAND_CSV
    master_path = settings.DATA_DIR / settings.DEMAND_MASTER_CSV
    training_path = merge_into_master(file_path, master_path, default_path)
    return _train_on_path(training_path)


def _train_on_path(training_path: Path) -> TrainedModel:
    """Core training logic, trains directly on an already-resolved CSV
    path (no merging). Used by both train_demand_model() and
    add_single_demand_record() so a single manual record doesn't get
    accidentally duplicated by re-running the merge step."""
    df = load_demand_df(training_path)

    exclude = TIME_FEATURES + [settings.DEMAND_TARGET_COL]
    extra_numeric = [
        c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude
    ]
    feature_cols = TIME_FEATURES + extra_numeric

    X = df[feature_cols].fillna(0)
    y = df[settings.DEMAND_TARGET_COL]

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(
    n_estimators=40,
    max_depth=10,
    min_samples_leaf=30,
    max_features=0.7,
    n_jobs=1,
    random_state=42,
)
    model.fit(X_tr, y_tr)

    y_pred = model.predict(X_te)
    trained = TrainedModel(
        model=model,
        feature_cols=feature_cols,
        mae=round(float(mean_absolute_error(y_te, y_pred)), 2),
        r2=round(float(r2_score(y_te, y_pred)), 4),
        rows_used=len(df),
    )
    model_store.set_demand(trained, df)
    return trained


def _predict_one_day(trained: TrainedModel, d: pd.Timestamp) -> float:
    base = {
        "day": d.day,
        "week": d.isocalendar()[1],
        "month": d.month,
        "year": d.year,
        "dayofweek": d.weekday(),
        "dayofyear": d.timetuple().tm_yday,
    }
    for fc in trained.feature_cols:
        if fc not in base:
            base[fc] = 0  # neutral default for extra numeric features
    row = pd.DataFrame([base])[trained.feature_cols]
    return max(0.0, float(trained.model.predict(row)[0]))


def forecast_demand(target_date: str) -> Tuple[str, float, float, float]:
    """Returns (reference_date, daily, weekly, monthly) forecasts."""
    trained = model_store.get_demand()
    if trained is None:
        raise ModelNotTrainedError(
            "Demand model has not been trained yet. Call /api/demand/train first."
        )

    try:
        ref_date = pd.to_datetime(target_date)
    except Exception:
        ref_date = pd.Timestamp.today().normalize()

    daily = _predict_one_day(trained, ref_date)
    weekly = sum(
        _predict_one_day(trained, ref_date + pd.Timedelta(days=i)) for i in range(7)
    )
    monthly = sum(
        _predict_one_day(trained, ref_date + pd.Timedelta(days=i)) for i in range(30)
    )
    return str(ref_date.date()), round(daily, 2), round(weekly, 2), round(monthly, 2)


def add_single_demand_record(record: dict, retrain: bool = True):
    """
    Appends ONE real, manually entered demand record to the master
    dataset (e.g. what you actually sold today). If retrain=True, the
    model is retrained immediately on the updated data so the new point
    is reflected right away; if False, it's just saved for the next
    scheduled/manual training run.

    Returns (rows_in_master, trained_or_none).
    """
    default_path = settings.DATA_DIR / settings.DEMAND_CSV
    master_path = settings.DATA_DIR / settings.DEMAND_MASTER_CSV
    append_single_record(record, master_path, default_path)

    rows_in_master = len(pd.read_csv(master_path))

    trained = None
    if retrain:
        trained = _train_on_path(master_path)

    return rows_in_master, trained