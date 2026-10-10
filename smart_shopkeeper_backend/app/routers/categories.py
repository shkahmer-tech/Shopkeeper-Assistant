"""
Category management routes.

  GET  /api/categories        - list your current categories
  POST /api/categories/add    - add a new category, optionally with a starting stock amount
  POST /api/categories/remove - remove an existing category (clears its stock too)
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import CategoryListResponse, CategoryRemoveRequest, CategoryRequest
from app.services import category_service

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("", response_model=CategoryListResponse)
def get_categories():
    return CategoryListResponse(categories=category_service.list_categories())


@router.post("/add", response_model=CategoryListResponse)
def add_category(payload: CategoryRequest):
    try:
        categories = category_service.add_category(payload.name, payload.initial_stock)
        return CategoryListResponse(
            categories=categories,
            message=f"'{payload.name}' added with {payload.initial_stock} units in stock.",
        )
    except category_service.CategoryAlreadyExistsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/remove", response_model=CategoryListResponse)
def remove_category(payload: CategoryRemoveRequest):
    try:
        categories = category_service.remove_category(payload.name)
        return CategoryListResponse(categories=categories, message=f"'{payload.name}' removed.")
    except category_service.CategoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc