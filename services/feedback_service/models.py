"""Feedback Service Data Models"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User Roles for RBAC"""
    ADMIN = "admin"
    CUSTOMER = "customer"
    RESTAURANT = "restaurant"
    GUEST = "guest"


class FeedbackBase(BaseModel):
    """Base feedback model"""
    order_id: str = Field(..., description="Order ID from Order Service")
    restaurant_id: str = Field(..., description="Restaurant ID from Restaurant Service")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    review_text: str = Field(..., min_length=10, max_length=500, description="Review text (10-500 chars)")


class FeedbackCreateRequest(BaseModel):
    """Feedback creation request (user_id and email come from headers)"""
    order_id: str = Field(..., description="Order ID from Order Service")
    restaurant_id: str = Field(..., description="Restaurant ID from Restaurant Service")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    review_text: str = Field(..., min_length=10, max_length=500, description="Review text (10-500 chars)")


class FeedbackUpdateRequest(BaseModel):
    """Feedback update request (only rating and review_text can be updated)"""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    review_text: str = Field(..., min_length=10, max_length=500, description="Review text (10-500 chars)")


class FeedbackCreate(FeedbackBase):
    """Feedback creation model (internal, includes user info)"""
    user_id: str = Field(..., description="Customer ID from Auth Service")
    email: str = Field(..., description="Customer email")


class FeedbackOut(FeedbackBase):
    """Feedback output model"""
    id: str
    user_id: str
    email: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool = False

    model_config = {"from_attributes": True}


class FeedbackList(BaseModel):
    """List of feedbacks for a restaurant"""
    restaurant_id: str
    feedbacks: list[FeedbackOut]
    total: int
    average_rating: float


class HealthResponse(BaseModel):
    """Service health check response"""
    status: str
    service: str
    database_mode: str  # "mock" or "connected"


class RBACContext(BaseModel):
    """RBAC Context from Gateway"""
    user_id: str
    email: str
    role: UserRole
