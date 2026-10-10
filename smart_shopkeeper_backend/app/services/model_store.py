"""
In-process model registry, with disk persistence.

Trained models are kept in memory for fast access during normal operation,
but every time a model finishes training it is also saved to disk with
joblib under MODELS_DIR. On server startup, main.py calls load_all()
here, which reloads any previously saved models — so you do NOT need to
retrain after restarting the server.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import joblib
import pandas as pd

from app.core.config import settings


@dataclass
class TrainedModel:
    model: object
    feature_cols: List[str]
    mae: float
    r2: float
    rows_used: int


class ModelStore:
    def __init__(self):
        self._demand: Optional[TrainedModel] = None
        self._delivery: Optional[TrainedModel] = None
        self._demand_raw_df: Optional[pd.DataFrame] = None  # kept for charting

    # ── Demand ──────────────────────────────────────────────────────
    def set_demand(self, trained: TrainedModel, raw_df: pd.DataFrame) -> None:
        self._demand = trained
        self._demand_raw_df = raw_df
        self._persist_demand()

    def get_demand(self) -> Optional[TrainedModel]:
        return self._demand

    def get_demand_raw_df(self) -> Optional[pd.DataFrame]:
        return self._demand_raw_df

    # ── Delivery ────────────────────────────────────────────────────
    def set_delivery(self, trained: TrainedModel) -> None:
        self._delivery = trained
        self._persist_delivery()

    def get_delivery(self) -> Optional[TrainedModel]:
        return self._delivery

    def status(self) -> dict:
        return {
            "demand_model_trained": self._demand is not None,
            "delivery_model_trained": self._delivery is not None,
        }

    # ── Disk persistence ───────────────────────────────────────────
    def _demand_path(self) -> Path:
        return settings.MODELS_DIR / "demand_model.joblib"

    def _delivery_path(self) -> Path:
        return settings.MODELS_DIR / "delivery_model.joblib"

    def _persist_demand(self) -> None:
        if self._demand is None:
            return
        joblib.dump(
            {
                "model": self._demand.model,
                "feature_cols": self._demand.feature_cols,
                "mae": self._demand.mae,
                "r2": self._demand.r2,
                "rows_used": self._demand.rows_used,
            },
            self._demand_path(),
        )

    def _persist_delivery(self) -> None:
        if self._delivery is None:
            return
        joblib.dump(
            {
                "model": self._delivery.model,
                "feature_cols": self._delivery.feature_cols,
                "mae": self._delivery.mae,
                "r2": self._delivery.r2,
                "rows_used": self._delivery.rows_used,
            },
            self._delivery_path(),
        )

    def load_all(self) -> None:
        """Called once at server startup to restore models saved in a
        previous run. The demand model also needs its raw dataframe back
        (for chart generation) — that's reloaded from the persisted master
        CSV, not from the joblib file itself."""
        if self._demand_path().exists():
            data = joblib.load(self._demand_path())
            self._demand = TrainedModel(
                model=data["model"],
                feature_cols=data["feature_cols"],
                mae=data["mae"],
                r2=data["r2"],
                rows_used=data["rows_used"],
            )
            try:
                from app.utils.data_loader import load_demand_df

                master_path = settings.DATA_DIR / settings.DEMAND_MASTER_CSV
                if master_path.exists():
                    self._demand_raw_df = load_demand_df(master_path)
            except Exception:
                self._demand_raw_df = None

        if self._delivery_path().exists():
            data = joblib.load(self._delivery_path())
            self._delivery = TrainedModel(
                model=data["model"],
                feature_cols=data["feature_cols"],
                mae=data["mae"],
                r2=data["r2"],
                rows_used=data["rows_used"],
            )


# Singleton used across the app (imported by services + routers)
model_store = ModelStore()