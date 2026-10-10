"""
AI Review service.

This is the new piece that wasn't in the original script. It takes the
structured output of the demand / inventory / delivery services and asks
Gemini to turn it into a short, plain-English business review — here is
the data, give me an assessment and concrete recommendations.

Uses Google's current `google-genai` SDK (the old `google-generativeai`
package is deprecated). Requires GEMINI_API_KEY (see .env.example).
"""

from app.core.config import settings
from app.models.schemas import (
    DeliveryPredictResponse,
    DemandForecastResponse,
    InventoryCheckResponse,
)

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:  # pragma: no cover
    genai = None
    genai_types = None


class AIReviewError(Exception):
    """Raised when the AI review can't be generated (missing key, API error)."""


REVIEW_SYSTEM_PROMPT = (
    "You are a business analyst assistant embedded in a shopkeeper's "
    "inventory and delivery dashboard. You are given structured demand "
    "forecast, inventory status, and delivery-time numbers. Write a short "
    "review (120-180 words) in plain, non-technical language: 1) a one-line "
    "verdict on overall health, 2) the single biggest risk to flag, and "
    "3) two concrete, specific actions the shopkeeper should take this week. "
    "No headers, no markdown, just clear prose a busy shop owner can read "
    "in 20 seconds."
)


def generate_ai_review(
    demand: DemandForecastResponse,
    inventory: InventoryCheckResponse,
    delivery: DeliveryPredictResponse,
) -> str:
    if genai is None:
        raise AIReviewError(
            "The 'google-genai' package is not installed. Run: pip install google-genai"
        )
    if not settings.GEMINI_API_KEY:
        raise AIReviewError(
            "GEMINI_API_KEY is not set. Add it to your .env file to enable AI reviews."
        )

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    user_prompt = f"""
Reference date: {demand.reference_date}

DEMAND FORECAST
- Predicted daily demand: {demand.predicted_daily} units
- Predicted weekly demand: {demand.predicted_weekly} units
- Predicted monthly demand: {demand.predicted_monthly} units

INVENTORY STATUS
- Current stock: {inventory.current_stock} units
- Status: {inventory.status}
- Units to reorder: {inventory.reorder_units}
- Action note: {inventory.action_note}

DELIVERY ESTIMATE
- Distance: {delivery.distance_km} km
- Traffic level: {delivery.traffic_level}
- Items on this delivery: {delivery.total_items} (total weight {delivery.total_weight_kg} kg)
- Estimated delivery time: {delivery.estimated_minutes} minutes

Write the review now.
""".strip()

    try:
        response = client.models.generate_content(
            model=settings.AI_REVIEW_MODEL,
            contents=user_prompt,
            config=genai_types.GenerateContentConfig(
                system_instruction=REVIEW_SYSTEM_PROMPT,
                max_output_tokens=400,
            ),
        )
        return (response.text or "").strip()
    except Exception as exc:  # noqa: BLE001
        raise AIReviewError(f"AI review generation failed: {exc}") from exc