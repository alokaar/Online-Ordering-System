from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends, Header, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database import get_database
from ..models import CartItem, CartOut, OrderCreate, OrderOut

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_current_user_id(x_user_id: str | None = Header(None)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-User-ID header required")
    return x_user_id


def order_doc_to_out(doc: dict) -> OrderOut:
    return OrderOut(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        items=doc["items"],
        total=doc["total"],
        status=doc["status"],
        delivery_address=doc["delivery_address"],
        phone_number=doc["phone_number"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


@router.get("/cart", response_model=CartOut)
async def get_cart(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
) -> CartOut:
    cart = await db.orders.find_one({"user_id": ObjectId(current_user_id), "status": "cart"})
    if cart is None:
        return CartOut(items=[], total=0.0)
    return CartOut(items=cart["items"], total=cart["total"])


@router.post("/cart/add", response_model=CartOut)
async def add_to_cart(
    item: CartItem,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
) -> CartOut:
    menu_item = await db.menu_items.find_one({"_id": ObjectId(item.menu_item_id)})
    if menu_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    if not menu_item.get("is_available", True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Menu item not available")

    cart_item = {
        "menu_item_id": item.menu_item_id,
        "name": menu_item["name"],
        "quantity": item.quantity,
        "price": menu_item["price"],
    }

    cart = await db.orders.find_one({"user_id": ObjectId(current_user_id), "status": "cart"})
    from datetime import datetime, timezone

    if cart is None:
        cart_doc = {
            "user_id": ObjectId(current_user_id),
            "items": [cart_item],
            "total": cart_item["price"] * cart_item["quantity"],
            "status": "cart",
            "delivery_address": "",
            "phone_number": "",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result = await db.orders.insert_one(cart_doc)
        cart = await db.orders.find_one({"_id": result.inserted_id})
    else:
        existing_items = cart["items"]
        item_found = False
        for existing_item in existing_items:
            if existing_item["menu_item_id"] == item.menu_item_id:
                existing_item["quantity"] += item.quantity
                item_found = True
                break
        if not item_found:
            existing_items.append(cart_item)

        total = sum(i["price"] * i["quantity"] for i in existing_items)
        await db.orders.update_one(
            {"_id": cart["_id"]},
            {
                "$set": {
                    "items": existing_items,
                    "total": total,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        cart = await db.orders.find_one({"_id": cart["_id"]})

    if cart is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cart update failed")

    return CartOut(items=cart["items"], total=cart["total"])


@router.delete("/cart/remove/{menu_item_id}", response_model=CartOut)
async def remove_from_cart(
    menu_item_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
) -> CartOut:
    cart = await db.orders.find_one({"user_id": ObjectId(current_user_id), "status": "cart"})
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    items = [item for item in cart["items"] if item["menu_item_id"] != menu_item_id]
    total = sum(i["price"] * i["quantity"] for i in items)

    await db.orders.update_one({"_id": cart["_id"]}, {"$set": {"items": items, "total": total}})
    return CartOut(items=items, total=total)


@router.put("/cart/update/{menu_item_id}", response_model=CartOut)
async def update_cart_item_quantity(
    menu_item_id: str,
    quantity: int,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
) -> CartOut:
    if quantity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be greater than 0")

    cart = await db.orders.find_one({"user_id": ObjectId(current_user_id), "status": "cart"})
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    items = cart["items"]
    item_found = False
    for item in items:
        if item["menu_item_id"] == menu_item_id:
            item["quantity"] = quantity
            item_found = True
            break

    if not item_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in cart")

    total = sum(i["price"] * i["quantity"] for i in items)
    from datetime import datetime, timezone

    await db.orders.update_one(
        {"_id": cart["_id"]},
        {"$set": {"items": items, "total": total, "updated_at": datetime.now(timezone.utc)}},
    )
    return CartOut(items=items, total=total)


@router.post("/cart/checkout", response_model=OrderOut)
async def checkout(
    order_data: OrderCreate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
) -> OrderOut:
    from datetime import datetime, timezone

    cart = await db.orders.find_one({"user_id": ObjectId(current_user_id), "status": "cart"})
    if cart is None or not cart.get("items"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    await db.orders.update_one(
        {"_id": cart["_id"]},
        {
            "$set": {
                "status": "pending",
                "delivery_address": order_data.delivery_address,
                "phone_number": order_data.phone_number,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    updated_order = await db.orders.find_one({"_id": cart["_id"]})
    if updated_order is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Order creation failed")

    return order_doc_to_out(updated_order)


@router.get("/", response_model=list[OrderOut])
async def get_user_orders(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
) -> list[OrderOut]:
    cursor = db.orders.find({"user_id": ObjectId(current_user_id), "status": {"$ne": "cart"}}).sort("created_at", -1)
    orders = await cursor.to_list(length=None)
    return [order_doc_to_out(order) for order in orders]


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user_id: Annotated[str, Depends(get_current_user_id)],
) -> OrderOut:
    try:
        obj_id = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID")

    order = await db.orders.find_one({"_id": obj_id, "user_id": ObjectId(current_user_id)})
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    return order_doc_to_out(order)
