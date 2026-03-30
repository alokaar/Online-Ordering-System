from fastapi import FastAPI, HTTPException
from models import DeliveryCreate, DeliveryUpdate
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
@app.get("/deliveries/{delivery_id}")
def get_delivery_by_id(delivery_id: str):

    delivery = DeliveryService.get_delivery_by_id(delivery_id)

    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    return delivery

# Retrieve all deliveries
@app.get("/deliveries")
def get_all_deliveries():
    deliveries = DeliveryService.get_all_deliveries()

    return deliveries

# Update delivery
@app.put("/deliveries/{delivery_id}")
def update_delivery(delivery_id: str, delivery: DeliveryUpdate):

    update_data = {k: v for k, v in delivery.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided for update")

    updated_count = DeliveryService.update_delivery(delivery_id, update_data)

    if updated_count == 0:
        raise HTTPException(status_code=404, detail="Delivery not found")

    return {
        "message": "Delivery updated successfully"
    }

# Delete a delivery
@app.delete("/delivery/{delivery_id}")
def delete_delivery(delivery_id: str):

    deleted_count = DeliveryService.delete_delivery(delivery_id)

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    return {
        "message" : "delivery deleted successfully"
    }