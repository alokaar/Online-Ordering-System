import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from schemas import RestaurantCreate, RestaurantUpdate, MenuItemCreate
from crud import (
    create_restaurant,
    get_all_restaurants,
    get_restaurant_by_id,
    update_restaurant,
    delete_restaurant,
    add_menu_item,
    get_menu,
    update_menu_item,
    delete_menu_item
)

load_dotenv()

app = FastAPI(
    title="Restaurant Service",
    description="Manage restaurants and menus",
    version="1.0.0"
)


@app.get("/")
def health_check():
    return {"message": "Restaurant Service is running"}


@app.post("/restaurants")
def create_restaurant_endpoint(restaurant: RestaurantCreate):
    return create_restaurant(restaurant.model_dump())


@app.get("/restaurants")
def get_restaurants_endpoint():
    return get_all_restaurants()


@app.get("/restaurants/{restaurant_id}")
def get_restaurant_endpoint(restaurant_id: str):
    restaurant = get_restaurant_by_id(restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@app.put("/restaurants/{restaurant_id}")
def update_restaurant_endpoint(restaurant_id: str, restaurant: RestaurantUpdate):
    updated = update_restaurant(restaurant_id, restaurant.model_dump())
    if not updated:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return updated


@app.delete("/restaurants/{restaurant_id}")
def delete_restaurant_endpoint(restaurant_id: str):
    deleted = delete_restaurant(restaurant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return {"message": "Restaurant deleted successfully"}


@app.post("/restaurants/{restaurant_id}/menu")
def add_menu_item_endpoint(restaurant_id: str, item: MenuItemCreate):
    created_item = add_menu_item(restaurant_id, item.model_dump())
    if not created_item:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return created_item


@app.get("/restaurants/{restaurant_id}/menu")
def get_menu_endpoint(restaurant_id: str):
    menu = get_menu(restaurant_id)
    if menu is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return menu


@app.put("/restaurants/{restaurant_id}/menu/{item_id}")
def update_menu_item_endpoint(restaurant_id: str, item_id: str, item: MenuItemCreate):
    updated_item = update_menu_item(restaurant_id, item_id, item.model_dump())
    if not updated_item:
        raise HTTPException(status_code=404, detail="Restaurant or menu item not found")
    return updated_item


@app.delete("/restaurants/{restaurant_id}/menu/{item_id}")
def delete_menu_item_endpoint(restaurant_id: str, item_id: str):
    deleted = delete_menu_item(restaurant_id, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Restaurant or menu item not found")
    return {"message": "Menu item deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)