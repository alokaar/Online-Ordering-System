from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from .database import get_database
from .models import MenuCategory, MenuItemCreate, MenuItemOut, MenuItemUpdate

router = APIRouter()


def menu_item_doc_to_out(doc: dict) -> MenuItemOut:
    return MenuItemOut(
        id=str(doc["_id"]),
        name=doc["name"],
        description=doc.get("description"),
        price=doc["price"],
        category=doc["category"],
        image_url=doc.get("image_url"),
        is_available=doc.get("is_available", True),
        created_at=doc["created_at"],
    )


@router.post("/", response_model=MenuItemOut, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    body: MenuItemCreate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> MenuItemOut:
    """Create a new menu item (admin only - for now, any authenticated user can create)."""
    from datetime import datetime, timezone

    doc = {
        "name": body.name,
        "description": body.description,
        "price": body.price,
        "category": body.category,
        "image_url": body.image_url,
        "is_available": body.is_available,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.menu_items.insert_one(doc)
    created = await db.menu_items.find_one({"_id": result.inserted_id})
    if created is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Menu item creation failed")
    return menu_item_doc_to_out(created)


@router.get("/", response_model=list[MenuItemOut])
async def get_menu_items(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    category: MenuCategory | None = None,
    available_only: bool = True,
) -> list[MenuItemOut]:
    """Get all menu items, optionally filtered by category."""
    query = {}
    if category:
        query["category"] = category.value
    if available_only:
        query["is_available"] = True

    cursor = db.menu_items.find(query).sort("created_at", -1)
    items = await cursor.to_list(length=None)
    return [menu_item_doc_to_out(item) for item in items]


@router.get("/category/{category}", response_model=list[MenuItemOut])
async def get_menu_items_by_category(
    category: MenuCategory,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    available_only: bool = True,
) -> list[MenuItemOut]:
    """Get all menu items under a specific category."""
    query = {"category": category.value}
    if available_only:
        query["is_available"] = True

    cursor = db.menu_items.find(query).sort("created_at", -1)
    items = await cursor.to_list(length=None)
    return [menu_item_doc_to_out(item) for item in items]


@router.get("/{item_id}", response_model=MenuItemOut)
async def get_menu_item(
    item_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> MenuItemOut:
    """Get a specific menu item by ID."""
    from bson import ObjectId

    try:
        obj_id = ObjectId(item_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item ID")

    item = await db.menu_items.find_one({"_id": obj_id})
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    return menu_item_doc_to_out(item)


@router.put("/{item_id}", response_model=MenuItemOut)
async def update_menu_item(
    item_id: str,
    body: MenuItemUpdate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> MenuItemOut:
    """Update a menu item."""
    from bson import ObjectId

    try:
        obj_id = ObjectId(item_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item ID")

    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    result = await db.menu_items.update_one({"_id": obj_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")

    updated = await db.menu_items.find_one({"_id": obj_id})
    if updated is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Update failed")
    return menu_item_doc_to_out(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(
    item_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> None:
    """Delete a menu item."""
    from bson import ObjectId

    try:
        obj_id = ObjectId(item_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item ID")

    result = await db.menu_items.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
