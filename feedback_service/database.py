"""Feedback Service Database Layer - Mock & Real DB Support"""
import logging
from datetime import datetime
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import DESCENDING
from pymongo.errors import DuplicateKeyError

from .config import settings
from .models import FeedbackCreate, FeedbackOut

logger = logging.getLogger(__name__)


# ============================================================================
# REAL DATABASE (MongoDB) - Production Database
# ============================================================================


class RealDatabase:
    """MongoDB database for feedback"""
    
    def __init__(self, db_collection: AsyncIOMotorCollection):
        self.collection = db_collection
    
    async def create_feedback(self, feedback_data: FeedbackCreate) -> FeedbackOut:
        """Create a new feedback in MongoDB"""
        feedback_doc = {
            "user_id": feedback_data.user_id,
            "email": feedback_data.email,
            "order_id": feedback_data.order_id,
            "restaurant_id": feedback_data.restaurant_id,
            "rating": feedback_data.rating,
            "review_text": feedback_data.review_text,
            "created_at": datetime.utcnow(),
            "updated_at": None,
            "is_deleted": False,
        }
        
        result = await self.collection.insert_one(feedback_doc)
        feedback_doc["id"] = str(result.inserted_id)
        
        logger.info(f"Created feedback {result.inserted_id} for restaurant {feedback_data.restaurant_id}")
        return self._to_feedback_out(feedback_doc)
    
    async def get_feedbacks_by_restaurant(self, restaurant_id: str) -> list[FeedbackOut]:
        """Get all non-deleted feedbacks for a restaurant from MongoDB"""
        cursor = self.collection.find({
            "restaurant_id": restaurant_id,
            "is_deleted": False
        }).sort("created_at", DESCENDING)
        
        feedbacks = []
        async for doc in cursor:
            feedbacks.append(self._to_feedback_out(doc))
        
        return feedbacks
    
    async def get_feedback_by_id(self, feedback_id: str) -> Optional[FeedbackOut]:
        """Get feedback by ID from MongoDB"""
        from bson import ObjectId
        
        try:
            doc = await self.collection.find_one({
                "_id": ObjectId(feedback_id),
                "is_deleted": False
            })
            if doc:
                return self._to_feedback_out(doc)
        except Exception as e:
            logger.warning(f"Error fetching feedback {feedback_id}: {e}")
        
        return None
    
    async def delete_feedback(self, feedback_id: str) -> bool:
        """Soft delete feedback from MongoDB"""
        from bson import ObjectId
        
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(feedback_id)},
                {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Deleted feedback {feedback_id}")
                return True
        except Exception as e:
            logger.warning(f"Error deleting feedback {feedback_id}: {e}")
        
        return False
    
    async def update_feedback(self, feedback_id: str, rating: int, review_text: str) -> Optional[FeedbackOut]:
        """Update feedback rating and review text"""
        from bson import ObjectId
        
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(feedback_id), "is_deleted": False},
                {"$set": {"rating": rating, "review_text": review_text, "updated_at": datetime.utcnow()}},
                return_document=True
            )
            
            if result:
                logger.info(f"Updated feedback {feedback_id}")
                return self._to_feedback_out(result)
        except Exception as e:
            logger.warning(f"Error updating feedback {feedback_id}: {e}")
        
        return None
    
    async def get_average_rating(self, restaurant_id: str) -> float:
        """Calculate average rating for a restaurant from MongoDB"""
        cursor = self.collection.find({
            "restaurant_id": restaurant_id,
            "is_deleted": False
        })
        
        ratings = []
        async for doc in cursor:
            ratings.append(doc["rating"])
        
        return sum(ratings) / len(ratings) if ratings else 0.0
    
    def _to_feedback_out(self, doc: dict) -> FeedbackOut:
        """Convert MongoDB document to FeedbackOut model"""
        return FeedbackOut(
            id=str(doc.get("_id", "")),
            user_id=doc["user_id"],
            email=doc["email"],
            order_id=doc["order_id"],
            restaurant_id=doc["restaurant_id"],
            rating=doc["rating"],
            review_text=doc["review_text"],
            created_at=doc["created_at"],
            updated_at=doc.get("updated_at"),
            is_deleted=doc.get("is_deleted", False),
        )


# ============================================================================
# MOCK DATABASE (In-Memory) - For Development Without MongoDB
# ============================================================================


class MockDatabase:
    """In-memory mock database for feedback"""
    
    def __init__(self):
        self.feedbacks: dict[str, dict] = {}  # {feedback_id: FeedbackData}
        self.id_counter = 1
        self._load_mock_data()
    
    def _load_mock_data(self):
        """Load example feedback data"""
        mock_feedbacks = [
            {
                "id": "fb_001",
                "user_id": "user_001",
                "email": "customer1@example.com",
                "order_id": "order_001",
                "restaurant_id": "rest_001",
                "rating": 5,
                "review_text": "Excellent pizza! Fresh ingredients and very tasty. Highly recommend this place.",
                "created_at": "2026-03-30T10:00:00",
                "updated_at": None,
                "is_deleted": False,
            },
            {
                "id": "fb_002",
                "user_id": "user_002",
                "email": "customer2@example.com",
                "order_id": "order_002",
                "restaurant_id": "rest_001",
                "rating": 4,
                "review_text": "Good quality food and fast delivery. Would order again definitely.",
                "created_at": "2026-03-29T14:30:00",
                "updated_at": None,
                "is_deleted": False,
            },
            {
                "id": "fb_003",
                "user_id": "user_003",
                "email": "customer3@example.com",
                "order_id": "order_003",
                "restaurant_id": "rest_001",
                "rating": 3,
                "review_text": "Average food. It was okay but nothing special compared to other options.",
                "created_at": "2026-03-28T18:15:00",
                "updated_at": None,
                "is_deleted": False,
            },
        ]
        
        for fb in mock_feedbacks:
            self.feedbacks[fb["id"]] = fb
            self.id_counter = max(self.id_counter, int(fb["id"].split("_")[1]) + 1)
    
    async def create_feedback(self, feedback_data: FeedbackCreate) -> FeedbackOut:
        """Create a new feedback"""
        feedback_id = f"fb_{self.id_counter:03d}"
        self.id_counter += 1
        
        from datetime import datetime
        feedback = {
            "id": feedback_id,
            "user_id": feedback_data.user_id,
            "email": feedback_data.email,
            "order_id": feedback_data.order_id,
            "restaurant_id": feedback_data.restaurant_id,
            "rating": feedback_data.rating,
            "review_text": feedback_data.review_text,
            "created_at": datetime.now().isoformat(),
            "updated_at": None,
            "is_deleted": False,
        }
        
        self.feedbacks[feedback_id] = feedback
        logger.info(f"Created feedback {feedback_id} for restaurant {feedback_data.restaurant_id}")
        return self._to_feedback_out(feedback)
    
    async def get_feedbacks_by_restaurant(self, restaurant_id: str) -> list[FeedbackOut]:
        """Get all non-deleted feedbacks for a restaurant"""
        feedbacks = [
            self._to_feedback_out(fb)
            for fb in self.feedbacks.values()
            if fb["restaurant_id"] == restaurant_id and not fb["is_deleted"]
        ]
        return sorted(feedbacks, key=lambda x: x.created_at, reverse=True)
    
    async def get_feedback_by_id(self, feedback_id: str) -> Optional[FeedbackOut]:
        """Get feedback by ID"""
        feedback = self.feedbacks.get(feedback_id)
        if feedback and not feedback["is_deleted"]:
            return self._to_feedback_out(feedback)
        return None
    
    async def delete_feedback(self, feedback_id: str) -> bool:
        """Soft delete feedback (mark as deleted)"""
        if feedback_id in self.feedbacks:
            self.feedbacks[feedback_id]["is_deleted"] = True
            logger.info(f"Deleted feedback {feedback_id}")
            return True
        return False
    
    async def update_feedback(self, feedback_id: str, rating: int, review_text: str) -> Optional[FeedbackOut]:
        """Update feedback rating and review text"""
        if feedback_id in self.feedbacks and not self.feedbacks[feedback_id]["is_deleted"]:
            from datetime import datetime
            self.feedbacks[feedback_id]["rating"] = rating
            self.feedbacks[feedback_id]["review_text"] = review_text
            self.feedbacks[feedback_id]["updated_at"] = datetime.now().isoformat()
            logger.info(f"Updated feedback {feedback_id}")
            return self._to_feedback_out(self.feedbacks[feedback_id])
        return None
    
    async def get_average_rating(self, restaurant_id: str) -> float:
        """Calculate average rating for a restaurant"""
        feedbacks = [
            fb["rating"]
            for fb in self.feedbacks.values()
            if fb["restaurant_id"] == restaurant_id and not fb["is_deleted"]
        ]
        return sum(feedbacks) / len(feedbacks) if feedbacks else 0.0
    
    def _to_feedback_out(self, feedback: dict) -> FeedbackOut:
        """Convert feedback dict to FeedbackOut model"""
        from datetime import datetime
        return FeedbackOut(
            id=feedback["id"],
            user_id=feedback["user_id"],
            email=feedback["email"],
            order_id=feedback["order_id"],
            restaurant_id=feedback["restaurant_id"],
            rating=feedback["rating"],
            review_text=feedback["review_text"],
            created_at=datetime.fromisoformat(feedback["created_at"]),
            updated_at=datetime.fromisoformat(feedback["updated_at"]) if feedback["updated_at"] else None,
            is_deleted=feedback["is_deleted"],
        )


# ============================================================================
# DATABASE SINGLETON
# ============================================================================


_mock_db: Optional[MockDatabase] = None
_real_db: Optional[RealDatabase] = None
_mongo_client: Optional[AsyncIOMotorClient] = None


def get_mock_database() -> MockDatabase:
    """Get mock database instance (singleton)"""
    global _mock_db
    if _mock_db is None:
        _mock_db = MockDatabase()
        logger.info("Mock database initialized")
    return _mock_db


async def init_real_database() -> RealDatabase:
    """Initialize real MongoDB connection"""
    global _real_db, _mongo_client
    
    try:
        _mongo_client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
        
        # Verify connection
        await _mongo_client.admin.command("ping")
        logger.info("✓ MongoDB connected successfully")
        
        # Get database and collection
        db = _mongo_client[settings.mongodb_db_name]
        collection = db["feedbacks"]
        
        # Create index on restaurant_id for better query performance
        await collection.create_index("restaurant_id")
        await collection.create_index([("created_at", DESCENDING)])
        
        _real_db = RealDatabase(collection)
        logger.info(f"✓ Real database initialized (using '{settings.mongodb_db_name}' database)")
        return _real_db
    
    except Exception as e:
        logger.error(f"✗ Failed to connect to MongoDB: {e}")
        _real_db = None
        raise


async def get_database() -> MockDatabase | RealDatabase:
    """Dependency for getting database instance"""
    if settings.use_mock_database:
        return get_mock_database()
    else:
        global _real_db
        if _real_db is None:
            await init_real_database()
        return _real_db


async def close_database() -> None:
    """Close database connections"""
    global _mongo_client, _real_db, _mock_db
    
    if _mongo_client:
        _mongo_client.close()
        logger.info("MongoDB connection closed")
    
    _real_db = None
    _mock_db = None
