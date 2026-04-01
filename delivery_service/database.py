from pymongo import MongoClient
from config import MONGODB_URI

client = MongoClient(MONGODB_URI)

db = client["food_ordering"]

delivery_collection = db["deliveries"]
driver_collection = db["drivers"]