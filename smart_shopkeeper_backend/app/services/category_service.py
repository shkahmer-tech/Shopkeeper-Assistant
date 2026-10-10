"""
Category management service.

Lets the shopkeeper maintain their OWN list of product categories (e.g.
Milk, Eggs, Snacks) — completely independent of whatever category values
happen to already exist in the training CSV.

THIS IS WHERE CATEGORIES CONNECT TO INVENTORY: adding a category here
automatically creates a stock entry for it in stock_service (starting at
whatever initial_stock you gave, or 0 if you didn't), and removing a
category here automatically deletes its stock entry too.
"""

import json
from pathlib import Path
from typing import List

from app.core.config import settings
from app.services import stock_service


class CategoryAlreadyExistsError(Exception):
    pass


class CategoryNotFoundError(Exception):
    pass


def _categories_path() -> Path:
    return settings.DATA_DIR / "categories.json"


def list_categories() -> List[str]:
    path = _categories_path()
    if not path.exists():
        return []
    with open(path, "r") as f:
        return json.load(f)


def _save_categories(categories: List[str]) -> None:
    path = _categories_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(categories, f, indent=2)


def add_category(name: str, initial_stock: float = 0.0) -> List[str]:
    """
    Adds a new category (e.g. "Milk") and creates its stock record in the
    same step, starting at initial_stock. This means a user can type a
    brand-new product name and its starting quantity together, in one action.
    """
    categories = list_categories()
    if name in categories:
        raise CategoryAlreadyExistsError(f"Category '{name}' already exists.")
    categories.append(name)
    _save_categories(categories)
    stock_service.set_current_stock(name, initial_stock)
    return categories


def remove_category(name: str) -> List[str]:
    categories = list_categories()
    if name not in categories:
        raise CategoryNotFoundError(f"Category '{name}' not found.")
    categories.remove(name)
    _save_categories(categories)
    stock_service.remove_category_stock(name)
    return categories