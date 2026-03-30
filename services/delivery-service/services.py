from database import delivery_collection
from bson import ObjectId

class DeliveryService:

    # Create a new delivery
    @staticmethod
    def create_delivery(data: dict):
        result = delivery_collection.insert_one(data)
        return str(result.inserted_id)
    
    # Retrieve delivery by ID
    @staticmethod
    def get_delivery_by_order_id(order_id: str):
        delivery = delivery_collection.find_one({"order_id": order_id})

        if delivery:
            delivery["id"] = str(delivery["_id"])
            del delivery["_id"]

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