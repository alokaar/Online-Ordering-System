from pymongo import MongoClient
from config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME

client = MongoClient(MONGODB_URI)

db = client[DATABASE_NAME]
delivery_collection = db[COLLECTION_NAME]