import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "food_ordering")
COLLECTION_NAME = os.getenv("RESTAURANT_COLLECTION", "restaurants")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
restaurant_collection = db[COLLECTION_NAME]