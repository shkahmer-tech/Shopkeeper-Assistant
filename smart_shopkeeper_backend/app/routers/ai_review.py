"""
AI Review route — the new capability added on top of the original script.

  POST /api/ai-review/generate - turn structured results into a plain-English review
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import AIReviewRequest, AIReviewResponse
from app.services import ai_review_service

router = APIRouter(prefix="/api/ai-review", tags=["AI Review"])


@router.post("/generate", response_model=AIReviewResponse)
def generate_review(payload: AIReviewRequest):
    try:
        review = ai_review_service.generate_ai_review(
            payload.demand, payload.inventory, payload.delivery
        )
        return AIReviewResponse(review=review)
    except ai_review_service.AIReviewError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
