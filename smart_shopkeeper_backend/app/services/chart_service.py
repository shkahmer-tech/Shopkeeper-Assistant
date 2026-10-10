"""
Visualisation service.

Refactor of PART 5 (save_charts) from the original ML_code.py. Generates
the same two-panel chart (demand trend + predicted daily/weekly/monthly
bars) but saves it to a unique file under outputs/charts so concurrent
API requests don't overwrite each other, and returns the path instead of
just printing it.
"""

import uuid

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from app.core.config import settings
from app.services.model_store import model_store


class ChartDataUnavailableError(Exception):
    """Raised when charting is requested before the demand model has data."""


def generate_demand_chart(daily: float, weekly: float, monthly: float) -> str:
    demand_df = model_store.get_demand_raw_df()
    if demand_df is None:
        raise ChartDataUnavailableError(
            "No demand data available. Call /api/demand/train first."
        )

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Smart Shopkeeper Assistant — Analytics", fontsize=14, fontweight="bold")

    # Chart 1 — Sales trend
    ax = axes[0]
    y_vals = demand_df[settings.DEMAND_TARGET_COL].values
    ax.plot(y_vals, alpha=0.35, color="#3498db", linewidth=1, label="Actual Demand")
    window = min(30, len(y_vals))
    rolling = pd.Series(y_vals).rolling(window).mean()
    ax.plot(rolling.values, color="#e74c3c", linewidth=2, label=f"{window}-Record Rolling Avg")
    ax.set_title("Demand Trend (Full Dataset)")
    ax.set_xlabel("Record Index")
    ax.set_ylabel(settings.DEMAND_TARGET_COL)
    ax.legend(fontsize=8)

    # Chart 2 — Predicted demand
    ax2 = axes[1]
    labels = ["Daily", "Weekly", "Monthly"]
    values = [daily, weekly, monthly]
    colors = ["#2ecc71", "#3498db", "#9b59b6"]
    bars = ax2.bar(labels, values, color=colors, width=0.5, edgecolor="white")
    for bar, val in zip(bars, values):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(values) * 0.01,
            f"{val:.0f}",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )
    ax2.set_title("Predicted Demand")
    ax2.set_ylabel("Units")

    plt.tight_layout()
    filename = f"shopkeeper_report_{uuid.uuid4().hex[:8]}.png"
    out_path = settings.CHARTS_DIR / filename
    plt.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)

    return str(out_path)
