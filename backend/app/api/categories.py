"""
Categories API - CRUD operations for knowledge map categories
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import os

router = APIRouter()

# Simple file-based storage for categories (can be upgraded to DB later)
CATEGORIES_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'categories.json')


class Category(BaseModel):
    id: str
    name: str
    color: str
    topics: List[str] = []
    count: int = 0
    isCustom: bool = True


class CategoriesResponse(BaseModel):
    categories: List[Category]


class CategoryCreate(BaseModel):
    name: str
    color: str
    topics: List[str] = []


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    topics: Optional[List[str]] = None


def _ensure_data_dir():
    """Ensure the data directory exists."""
    data_dir = os.path.dirname(CATEGORIES_FILE)
    os.makedirs(data_dir, exist_ok=True)


def _load_categories() -> List[dict]:
    """Load categories from file."""
    _ensure_data_dir()
    if os.path.exists(CATEGORIES_FILE):
        try:
            with open(CATEGORIES_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_categories(categories: List[dict]):
    """Save categories to file."""
    _ensure_data_dir()
    with open(CATEGORIES_FILE, 'w') as f:
        json.dump(categories, f, indent=2)


@router.get("/", response_model=CategoriesResponse)
async def get_categories():
    """Get all categories."""
    categories = _load_categories()
    return CategoriesResponse(categories=[Category(**c) for c in categories])


@router.put("/")
async def sync_categories(data: CategoriesResponse):
    """Sync categories from frontend (full replace)."""
    categories = [c.dict() for c in data.categories]
    _save_categories(categories)
    return {"status": "ok", "count": len(categories)}


@router.post("/", response_model=Category)
async def create_category(category: CategoryCreate):
    """Create a new category."""
    import uuid

    categories = _load_categories()

    # Check for duplicate names
    if any(c['name'].lower() == category.name.lower() for c in categories):
        raise HTTPException(status_code=400, detail="Category with this name already exists")

    new_category = {
        "id": f"cat-{uuid.uuid4().hex[:12]}",
        "name": category.name,
        "color": category.color,
        "topics": category.topics,
        "count": 0,
        "isCustom": True,
    }

    categories.append(new_category)
    _save_categories(categories)

    return Category(**new_category)


@router.patch("/{category_id}", response_model=Category)
async def update_category(category_id: str, updates: CategoryUpdate):
    """Update a category."""
    categories = _load_categories()

    for i, cat in enumerate(categories):
        if cat['id'] == category_id:
            if updates.name is not None:
                cat['name'] = updates.name
            if updates.color is not None:
                cat['color'] = updates.color
            if updates.topics is not None:
                cat['topics'] = updates.topics

            categories[i] = cat
            _save_categories(categories)
            return Category(**cat)

    raise HTTPException(status_code=404, detail="Category not found")


@router.delete("/{category_id}")
async def delete_category(category_id: str):
    """Delete a category."""
    categories = _load_categories()

    initial_count = len(categories)
    categories = [c for c in categories if c['id'] != category_id]

    if len(categories) == initial_count:
        raise HTTPException(status_code=404, detail="Category not found")

    _save_categories(categories)
    return {"status": "deleted", "id": category_id}


@router.post("/{category_id}/topics")
async def add_topic(category_id: str, topic: str):
    """Add a topic to a category."""
    categories = _load_categories()

    for i, cat in enumerate(categories):
        if cat['id'] == category_id:
            if topic not in cat['topics']:
                cat['topics'].append(topic)
                categories[i] = cat
                _save_categories(categories)
            return {"status": "ok", "topics": cat['topics']}

    raise HTTPException(status_code=404, detail="Category not found")


@router.delete("/{category_id}/topics/{topic}")
async def remove_topic(category_id: str, topic: str):
    """Remove a topic from a category."""
    categories = _load_categories()

    for i, cat in enumerate(categories):
        if cat['id'] == category_id:
            cat['topics'] = [t for t in cat['topics'] if t != topic]
            categories[i] = cat
            _save_categories(categories)
            return {"status": "ok", "topics": cat['topics']}

    raise HTTPException(status_code=404, detail="Category not found")
