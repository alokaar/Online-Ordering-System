import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "online_food_ordering")
COLLECTION_NAME = os.getenv("RESTAURANT_COLLECTION", "restaurants")

if not MONGO_URI:
    raise ValueError("MONGO_URI is not set in the .env file")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
restaurant_collection = db[COLLECTION_NAME]