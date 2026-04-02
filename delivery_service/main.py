from fastapi import FastAPI, HTTPException
from models import CreateDelivery
from service import DeliveryService
from bson import ObjectId
from database import delivery_collection
from models import DeliveryUpdate

app = FastAPI(title="Delivery Service")

# Create a new delivery
@app.post("/deliveries")
async def create_delivery(delivery: CreateDelivery):

    try:
        delivery_id = await DeliveryService.create_delivery(delivery.dict())
        return {"message": "Delivery created successfully.", "id": delivery_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    
# Retreive all deliveries
@app.get("/deliveries")
def get_all():
    return DeliveryService.get_all_deliveries()


# Retrive delivery by id
@app.get("/deliveries/id/{delivery_id}")
def get_delivery_by_id(delivery_id: str):
    d = delivery_collection.find_one({"_id": ObjectId(delivery_id)})

    if not d:
        raise HTTPException(status_code=404, detail="Not found")

    d["id"] = str(d["_id"])
    del d["_id"]

    d["created_at"] = str(d["created_at"])
    d["updated_at"] = str(d["updated_at"])

    return d


# Update delivery details
@app.put("/deliveries/id/{delivery_id}")
async def update_delivery(delivery_id: str, delivery: DeliveryUpdate):

    updated_count = DeliveryService.update_delivery(
        delivery_id,
        delivery.dict()
    )

    if updated_count == 0:
        raise HTTPException(status_code=404, detail="Delivery not found or no changes")
    
    return {"message": "Delivery updated successfully"}

# Delete delivery
@app.delete("/deliveries/{delivery_id}")
async def delete_delivery(delivery_id: str):

    deleted_count = DeliveryService.delete_delivery(delivery_id)

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Delivery not found")

    return {"message": "Delivery details deleted successfully"}