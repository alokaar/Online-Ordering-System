import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8008")

DATABASE_NAME = "food_ordering"
COLLECTION_NAME = "deliveries"