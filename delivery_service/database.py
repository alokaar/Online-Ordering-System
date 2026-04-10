from pymongo import MongoClient
from .config import MONGODB_URI, DATABASE_NAME

client = MongoClient(MONGODB_URI)

db = client[DATABASE_NAME]
order_db = client["order_db"]

delivery_collection = db["deliveries"]
driver_collection = db["drivers"]