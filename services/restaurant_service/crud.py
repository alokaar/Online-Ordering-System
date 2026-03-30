from uuid import uuid4
from database import restaurant_collection


def serialize_restaurant(doc):
    return {
        "id": doc["id"],
        "name": doc["name"],
        "description": doc.get("description", ""),
        "address": doc["address"],
        "phone": doc["phone"],
        "cuisine": doc["cuisine"],
        "is_active": doc.get("is_active", True),
        "menu": doc.get("menu", [])
    }


def create_restaurant(data: dict):
    restaurant = {
        "id": str(uuid4()),
        "name": data["name"],
        "description": data.get("description", ""),
        "address": data["address"],
        "phone": data["phone"],
        "cuisine": data["cuisine"],
        "is_active": data.get("is_active", True),
        "menu": []
    }
    restaurant_collection.insert_one(restaurant)
    return restaurant


def get_all_restaurants():
    return [serialize_restaurant(doc) for doc in restaurant_collection.find()]


def get_restaurant_by_id(restaurant_id: str):
    doc = restaurant_collection.find_one({"id": restaurant_id})
    return serialize_restaurant(doc) if doc else None


def update_restaurant(restaurant_id: str, data: dict):
    update_data = {k: v for k, v in data.items() if v is not None}
    result = restaurant_collection.update_one(
        {"id": restaurant_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        return None
    return get_restaurant_by_id(restaurant_id)


def delete_restaurant(restaurant_id: str):
    result = restaurant_collection.delete_one({"id": restaurant_id})
    return result.deleted_count > 0


def add_menu_item(restaurant_id: str, item_data: dict):
    item = {
        "id": str(uuid4()),
        "name": item_data["name"],
        "description": item_data.get("description", ""),
        "price": item_data["price"],
        "category": item_data.get("category", "General"),
        "available": item_data.get("available", True)
    }

    result = restaurant_collection.update_one(
        {"id": restaurant_id},
        {"$push": {"menu": item}}
    )

    if result.matched_count == 0:
        return None
    return item


def get_menu(restaurant_id: str):
    restaurant = get_restaurant_by_id(restaurant_id)
    if not restaurant:
        return None
    return restaurant.get("menu", [])


def update_menu_item(restaurant_id: str, item_id: str, data: dict):
    restaurant = restaurant_collection.find_one({"id": restaurant_id})
    if not restaurant:
        return None

    menu = restaurant.get("menu", [])
    updated = False

    for item in menu:
        if item["id"] == item_id:
            for key, value in data.items():
                if value is not None:
                    item[key] = value
            updated = True
            break

    if not updated:
        return None

    restaurant_collection.update_one(
        {"id": restaurant_id},
        {"$set": {"menu": menu}}
    )
    return next((item for item in menu if item["id"] == item_id), None)


def delete_menu_item(restaurant_id: str, item_id: str):
    result = restaurant_collection.update_one(
        {"id": restaurant_id},
        {"$pull": {"menu": {"id": item_id}}}
    )
    return result.modified_count > 0