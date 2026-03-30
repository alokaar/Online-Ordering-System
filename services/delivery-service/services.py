from database import delivery_collection
from bson import ObjectId
from datetime import datetime

class DeliveryService:

    # Create a new delivery
    @staticmethod
    def create_delivery(data: dict):

        current = datetime.utcnow()

        data["created_at"] = current
        data["updated_at"] = current

        result = delivery_collection.insert_one(data)
        return str(result.inserted_id)
    
    # Retrieve delivery by ID
    @staticmethod
    def get_delivery_by_id(delivery_id: str):
        delivery = delivery_collection.find_one({"_id": ObjectId(delivery_id)})

        if delivery:
            delivery["id"] = str(delivery["_id"])
            del delivery["_id"]

            if "created_at" in delivery:
                delivery["created_at"] = str(delivery["created_at"])

            if "updated_at" in delivery:
                delivery["updated_at"] = str(delivery["updated_at"])

        return delivery

    # Retrieve all deliveries
    @staticmethod
    def get_all_deliveries():
        deliveries = []

        for delivery in delivery_collection.find():
            delivery["id"] = str(delivery["_id"])
            del delivery["_id"]
            deliveries.append(delivery)

        return deliveries
    
    # Update delivery details
    @staticmethod
    def update_delivery(delivery_id:str, data: dict):

        data["updated_at"] = datetime.utcnow()

        updated = delivery_collection.update_one(
            {"_id": ObjectId(delivery_id)},
            {"$set": data}
        )

        return updated.modified_count
    
    # Delete a delivery
    @staticmethod
    def delete_delivery(delivery_id : str):
        deleted = delivery_collection.delete_one(
            {"_id": ObjectId(delivery_id)}
        )

        return deleted.deleted_count