import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL")

DATABASE_NAME = "food_ordering"
COLLECTION_NAME = "deliveries"