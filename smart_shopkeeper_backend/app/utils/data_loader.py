"""
Data loading & preprocessing helpers.

Refactor of PART 1 (load_demand) and PART 4 (load_delivery) from the
original ML_code.py, plus two additions used by the "cumulative dataset"
feature: merge_into_master() for bulk CSV uploads, and
append_single_record() for one manually entered data point.
"""

from pathlib import Path
from typing import Optional

import pandas as pd
from sklearn.preprocessing import LabelEncoder

from app.core.config import settings


class DataLoadError(Exception):
    """Raised when a CSV is missing or malformed — caught by routers and
    turned into a clean HTTP 400/404 response."""


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise DataLoadError(
            f"File not found: '{path.name}'. Place it in the /data folder "
            f"or upload it via the training endpoint."
        )
    return pd.read_csv(path)


def merge_into_master(new_file_path: Optional[Path], master_path: Path, default_path: Path) -> Path:
    """
    Cumulative dataset builder used by both bulk-CSV train endpoints.

    - If the master file doesn't exist yet, it's seeded from either the
      newly uploaded file or the default configured CSV in /data.
    - If the master file already exists and a new file was uploaded, the
      new rows are appended to it (duplicates dropped) and saved back.
    - Returns the path to train on (always the master file going forward).
    """
    master_path.parent.mkdir(parents=True, exist_ok=True)

    if not master_path.exists():
        seed_path = new_file_path if new_file_path is not None else default_path
        if not seed_path.exists():
            raise DataLoadError(
                f"No dataset available yet. Upload a CSV or place one at '{default_path}'."
            )
        seed_df = pd.read_csv(seed_path)
        seed_df.to_csv(master_path, index=False)
        return master_path

    if new_file_path is not None:
        existing_df = pd.read_csv(master_path)
        new_df = pd.read_csv(new_file_path)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
        combined.drop_duplicates(inplace=True)
        combined.to_csv(master_path, index=False)

    return master_path


def append_single_record(record: dict, master_path: Path, default_path: Path) -> Path:
    """
    Appends ONE manually entered record (a dict of column -> value) to the
    master dataset, creating the master file first (seeded from the
    default CSV) if it doesn't exist yet. Used when a user submits a
    single real data point through the API instead of uploading a CSV.
    """
    master_path.parent.mkdir(parents=True, exist_ok=True)

    if not master_path.exists():
        if default_path.exists():
            base_df = pd.read_csv(default_path)
        else:
            base_df = pd.DataFrame(columns=list(record.keys()))
        base_df.to_csv(master_path, index=False)

    existing_df = pd.read_csv(master_path)
    new_row_df = pd.DataFrame([record])
    combined = pd.concat([existing_df, new_row_df], ignore_index=True)
    combined.to_csv(master_path, index=False)
    return master_path


def load_demand_df(file_path: Optional[Path] = None) -> pd.DataFrame:
    """Load + preprocess the demand/inventory dataset."""
    path = file_path or (settings.DATA_DIR / settings.DEMAND_CSV)
    df = _read_csv(path)

    for col in (settings.DEMAND_DATE_COL, settings.DEMAND_TARGET_COL):
        if col not in df.columns:
            raise DataLoadError(
                f"Column '{col}' not found in demand dataset. "
                f"Available columns: {list(df.columns)}"
            )

    # Clean target
    df[settings.DEMAND_TARGET_COL] = pd.to_numeric(
        df[settings.DEMAND_TARGET_COL], errors="coerce"
    )
    df.dropna(subset=[settings.DEMAND_TARGET_COL], inplace=True)

    # Parse date & extract time features
    df[settings.DEMAND_DATE_COL] = pd.to_datetime(
        df[settings.DEMAND_DATE_COL], errors="coerce"
    )
    df.dropna(subset=[settings.DEMAND_DATE_COL], inplace=True)
    df["day"] = df[settings.DEMAND_DATE_COL].dt.day
    df["week"] = df[settings.DEMAND_DATE_COL].dt.isocalendar().week.astype(int)
    df["month"] = df[settings.DEMAND_DATE_COL].dt.month
    df["year"] = df[settings.DEMAND_DATE_COL].dt.year
    df["dayofweek"] = df[settings.DEMAND_DATE_COL].dt.dayofweek
    df["dayofyear"] = df[settings.DEMAND_DATE_COL].dt.dayofyear
    df.sort_values(settings.DEMAND_DATE_COL, inplace=True)

    # Encode categoricals
    le = LabelEncoder()
    for col in df.select_dtypes(include=["object", "category"]).columns:
        df[col] = le.fit_transform(df[col].astype(str))

    df.reset_index(drop=True, inplace=True)
    if df.empty:
        raise DataLoadError("Demand dataset is empty after cleaning.")
    return df


def load_delivery_df(file_path: Optional[Path] = None) -> pd.DataFrame:
    """Load + preprocess the delivery dataset."""
    path = file_path or (settings.DATA_DIR / settings.DELIVERY_CSV)
    df = _read_csv(path)

    required = [
        settings.DELIVERY_DIST_COL,
        settings.DELIVERY_TRAFFIC_COL,
        settings.DELIVERY_TARGET_COL,
    ]
    for col in required:
        if col not in df.columns:
            raise DataLoadError(
                f"Column '{col}' not found in delivery dataset. "
                f"Available columns: {list(df.columns)}"
            )

    keep = list(required)
    if settings.DELIVERY_WEATHER_COL and settings.DELIVERY_WEATHER_COL in df.columns:
        keep.append(settings.DELIVERY_WEATHER_COL)
    for extra_col in settings.DELIVERY_EXTRA_FEATURES:
        if extra_col in df.columns:
            keep.append(extra_col)

    df = df[keep].copy()
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df.dropna(subset=[settings.DELIVERY_TARGET_COL], inplace=True)
    if df.empty:
        raise DataLoadError("Delivery dataset is empty after cleaning.")
    return df