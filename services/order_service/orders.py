from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from .database import get_database
from .models import CartOut, CartItem, OrderCreate, OrderOut

router = APIRouter()


def order_doc_to_out(doc: dict) -> OrderOut:
    return OrderOut(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        items=doc["items"],
        total=doc["total"],
        status=doc["status"],
        delivery_address=doc.get("delivery_address", ""),
        phone_number=doc.get("phone_number", ""),
        full_name=doc.get("full_name"),
        email=doc.get("email"),
        receiver_details=doc.get("receiver_details"),
        special_ticket_instructions=doc.get("special_ticket_instructions"),
        payment_method=doc.get("payment_method"),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


@router.get("/cart", response_model=CartOut)
async def get_cart(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user_id: str = "000000000000000000000000",
) -> CartOut:
    """Get current user's cart (active order with status 'cart')."""
    from bson import ObjectId

    cart = await db.orders.find_one({
        "user_id": ObjectId(user_id),
        "status": "cart"
    })
    if cart is None:
        return CartOut(items=[], total=0.0)

    # Ensure all cart items have names
    items_with_names = []
    for item in cart["items"]:
        if "name" not in item or not item["name"]:
            # Fetch name from menu_items if missing
            menu_item = await db.menu_items.find_one({"_id": ObjectId(item["menu_item_id"])})
            item_name = menu_item["name"] if menu_item else f"Item {item['menu_item_id']}"
            item_copy = item.copy()
            item_copy["name"] = item_name
            items_with_names.append(item_copy)
        else:
            items_with_names.append(item)

    # Update cart in database if names were added
    if len(items_with_names) != len(cart["items"]):
        await db.orders.update_one(
            {"_id": cart["_id"]},
            {"$set": {"items": items_with_names}}
        )

    return CartOut(items=items_with_names, total=cart["total"])


@router.post("/cart/add", response_model=CartOut)
async def add_to_cart(
    item: CartItem,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user_id: str = "000000000000000000000000",
) -> CartOut:
    """Add item to cart. Creates cart if doesn't exist."""
    from bson import ObjectId
    from datetime import datetime, timezone

    # Verify menu item exists and is available
    menu_item = await db.menu_items.find_one({"_id": ObjectId(item.menu_item_id)})
    if menu_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    if not menu_item.get("is_available", True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Menu item not available")

    # Create cart item with correct price from menu
    cart_item = {
        "menu_item_id": item.menu_item_id,
        "name": menu_item["name"],  # Include item name
        "quantity": item.quantity,
        "price": menu_item["price"]  # Use actual price from menu item
    }

    # Get or create cart
    cart = await db.orders.find_one({
        "user_id": ObjectId(user_id),
        "status": "cart"
    })

    if cart is None:
        # Create new cart
        cart_doc = {
            "user_id": ObjectId(user_id),
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
        # Update existing cart
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
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        cart = await db.orders.find_one({"_id": cart["_id"]})

    if cart is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cart update failed")

    return CartOut(items=cart["items"], total=cart["total"])


@router.delete("/cart/remove/{menu_item_id}", response_model=CartOut)
async def remove_from_cart(
    menu_item_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user_id: str = "000000000000000000000000",
) -> CartOut:
    """Remove item from cart."""
    from bson import ObjectId

    cart = await db.orders.find_one({
        "user_id": ObjectId(user_id),
        "status": "cart"
    })
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    items = [item for item in cart["items"] if item["menu_item_id"] != menu_item_id]
    total = sum(i["price"] * i["quantity"] for i in items)

    await db.orders.update_one(
        {"_id": cart["_id"]},
        {
            "$set": {
                "items": items,
                "total": total,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return CartOut(items=items, total=total)


@router.put("/cart/update/{menu_item_id}", response_model=CartOut)
async def update_cart_item_quantity(
    menu_item_id: str,
    quantity: int,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user_id: str = "000000000000000000000000",
) -> CartOut:
    """Update quantity of item in cart."""
    from bson import ObjectId
    from datetime import datetime, timezone

    if quantity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be greater than 0")

    cart = await db.orders.find_one({
        "user_id": ObjectId(user_id),
        "status": "cart"
    })
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

    await db.orders.update_one(
        {"_id": cart["_id"]},
        {
            "$set": {
                "items": items,
                "total": total,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return CartOut(items=items, total=total)


@router.post("/checkout", response_model=OrderOut)
async def checkout(
    order_data: OrderCreate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user_id: str = "000000000000000000000000",
) -> OrderOut:
    """Convert cart to order."""
    from bson import ObjectId
    from datetime import datetime, timezone

    cart = await db.orders.find_one({
        "user_id": ObjectId(user_id),
        "status": "cart"
    })
    if cart is None or not cart["items"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    checkout_updates = order_data.model_dump(mode='json')
    checkout_updates["status"] = "pending"
    checkout_updates["updated_at"] = datetime.now(timezone.utc)

    # Update cart to order
    await db.orders.update_one(
        {"_id": cart["_id"]},
        {"$set": checkout_updates}
    )

    updated_order = await db.orders.find_one({"_id": cart["_id"]})
    if updated_order is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Order creation failed")

    return order_doc_to_out(updated_order)


@router.get("/orders", response_model=list[OrderOut])
async def get_user_orders(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user_id: str = "000000000000000000000000",
) -> list[OrderOut]:
    """Get user's order history."""
    from bson import ObjectId

    cursor = db.orders.find({
        "user_id": ObjectId(user_id),
        "status": {"$ne": "cart"}
    }).sort("created_at", -1)
    orders = await cursor.to_list(length=None)
    return [order_doc_to_out(order) for order in orders]


@router.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user_id: str = "000000000000000000000000",
) -> OrderOut:
    """Get specific order details."""
    from bson import ObjectId

    try:
        obj_id = ObjectId(order_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID")

    order = await db.orders.find_one({
        "_id": obj_id,
        "user_id": ObjectId(user_id)
    })
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    return order_doc_to_out(order)
