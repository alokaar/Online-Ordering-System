from fastapi import FastAPI, HTTPException
from models import DeliveryCreate, DeliveryOut
from services import DeliveryService

app = FastAPI(title="Delivery Service")

# Create a new delivery
@app.post("/deliveries", response_model=dict)
def create_delivery(delivery: DeliveryCreate):
    delivery_dict = delivery.dict()

    delivery_id = DeliveryService.create_delivery(delivery_dict)

    return {
        "message": "Successfully added the  delivery",
        "delivery_id": delivery_id
    }

# Retreive delivery by ID
@app.get("/deliveries/{order_id}")
def get_delivery_by_order_id(order_id: str):
    delivery = DeliveryService.get_delivery_by_order_id(order_id)

    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    return delivery

# Retrieve all deliveries
@app.get("/deliveries")
def get_all_deliveries():
    deliveries = DeliveryService.get_all_deliveries()

    return deliveries