import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "food_ordering")
COLLECTION_NAME = os.getenv("RESTAURANT_COLLECTION", "restaurants")

client = MongoClient(MONGO_URI)

db_name = "restaurant_db"
db = client[db_name]
restaurant_collection = db[COLLECTION_NAME]