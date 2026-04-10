from pymongo import MongoClient
from .config import MONGODB_URI

client = MongoClient(MONGODB_URI)

db_name = "delivery_db"
db = client[db_name]

delivery_collection = db["deliveries"]
driver_collection = db["drivers"]