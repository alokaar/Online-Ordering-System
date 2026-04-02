import random
import httpx

from datetime import datetime
from bson import ObjectId
from database import delivery_collection, driver_collection
from config import ORDER_SERVICE_URL

class DeliveryService:

    # Helper function to convert delivery id
    @staticmethod
    def format_delivery(d):
        d["id"] = str(d["_id"])
        del d["_id"]

        d["created_at"] = str(d["created_at"])
        d["updated_at"] = str(d["updated_at"])

        return d
 
    # Import order details from order service
    @staticmethod
    async def get_order_details(order_id: str, user_id: str):

        try:
            url = f"{ORDER_SERVICE_URL}/orders/{order_id}"

            params = {
                "user_id": user_id
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)

            if response.status_code != 200:
                print("Order Service response:", response.text)
                return None
            
            order = response.json()

            return {
                "full_name": order.get("full_name"),
                "phone_number": order.get("phone_number"),
                "delivery_address": order.get("delivery_address"),
                "total": order.get("total"),
                "payment_method": order.get("payment_method"),
                "reciever_details": order.get("receiver_details"),
            }

        except Exception as e:
            print("Order Service Error: ", e)
            return None


    # Assign a random driver
    @staticmethod
    def assign_driver():
        drivers = list(driver_collection.find())
        return random.choice(drivers) if drivers else None
    

    # Create a new delivery
    @staticmethod
    async def create_delivery(data: dict):

        order_data = await DeliveryService.get_order_details(
            data["order_id"],
            data["user_id"]
        )

        if not order_data:
            raise Exception("Order not found. please check the order number and user id.")
        
        driver = DeliveryService.assign_driver()
        now = datetime.utcnow()

        delivery = {
            "order_id": data["order_id"],
            "status": "Order Ready.",
            "location": data["location"],
            "estimated_time": data["estimated_time"],

            **order_data,

            "driver_name": driver["name"] if driver else "Not Assigned",
            "driver_phone": driver["phone"] if driver else "N/A",

            "created_at": now,
            "updated_at": now
        }

        result = delivery_collection.insert_one(delivery)
        return str(result.inserted_id)


    # Retreive all orders
    @staticmethod
    def get_all_deliveries():
        deliveries = []

        for d in delivery_collection.find():
            d["id"] = str(d["_id"])
            del d["_id"]

            d["created_at"] = str(d["created_at"])
            d["updated_at"] = str(d["updated_at"])

            deliveries.append(d)

        return deliveries
    
    # Retrieve delivery by delivery id
    @staticmethod
    def get_delivery_by_id(delivery_id: str):
        try:
            d = delivery_collection.find_one({"_id": ObjectId(delivery_id)})
            return DeliveryService.format_delivery(d) if d else None
        
        except:
            return None


    # Update delivery details
    @staticmethod
    def update_delivery(delivery_id: str, data:dict):

        try:
            obj_id = ObjectId(delivery_id)
        except:
            return 0
        
        update_data = {k: v for k, v in data.items() if v is not None}

        if not update_data:
            return 0
        
        update_data["updated_at"] = datetime.utcnow()

        result = delivery_collection.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )

        return result.modified_count
    

    # Delete Delivery
    @staticmethod
    def delete_delivery(delivery_id: str):

        try:
            obj_id = ObjectId(delivery_id)
        except:
            return 0

        result = delivery_collection.delete_one({"_id": obj_id})

        return result.deleted_count