"""Feedback Service Microservice — Main Entry Point
Handles customer feedback, ratings, and reviews for orders
Runs on Port 8004
"""

import logging
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException, status

from .config import settings
from .database import get_database, close_database, init_real_database
from .models import (
    FeedbackCreate,
    FeedbackCreateRequest,
    FeedbackList,
    FeedbackOut,
    FeedbackUpdateRequest,
    HealthResponse,
    RBACContext,
)
from .service import (
    FeedbackService,
    RBACService,
    get_feedback_service,
    get_rbac_context,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown"""
    # Startup
    if not settings.use_mock_database:
        try:
            await init_real_database()
            logger.info("✓ Feedback Service started with MongoDB")
        except Exception as e:
            logger.error(f"✗ Failed to start service: {e}")
            raise
    else:
        logger.info("✓ Feedback Service started with Mock Database")
    
    yield
    
    # Shutdown
    await close_database()
    logger.info("Feedback Service shut down")


# Create FastAPI app
app = FastAPI(
    title="Feedback Service",
    description="Microservice for managing customer feedback, ratings, and reviews",
    version="0.1.0",
    lifespan=lifespan,
)


# ============================================================================
# HEALTH & SYSTEM ENDPOINTS
# ============================================================================


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(db: Annotated[object, Depends(get_database)]) -> HealthResponse:
    """Service health check"""
    database_mode = "mock" if settings.use_mock_database else "connected"
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        database_mode=database_mode,
    )


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    """Service information"""
    return {
        "message": "Feedback Service — use /docs for Swagger UI",
        "version": "0.1.0",
        "service": settings.service_name,
        "database_mode": "mock" if settings.use_mock_database else "mongodb",
        "docs": "/docs",
    }


# ============================================================================
# FEEDBACK ENDPOINTS
# ============================================================================


@app.post(
    "/feedbacks",
    response_model=FeedbackOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Feedback"],
)
async def create_feedback(
    feedback_request: FeedbackCreateRequest,
    rbac_context: Annotated[RBACContext, Depends(get_rbac_context)],
    service: Annotated[FeedbackService, Depends(get_feedback_service)],
) -> FeedbackOut:
    """
    Create new feedback for an order.
    
    **Access:** CUSTOMER only
    
    - **order_id**: ID from Order Service (required)
    - **restaurant_id**: ID from Restaurant Service (required)
    - **rating**: 1-5 stars
    - **review_text**: 10-500 characters
    """
    rbac = RBACService(rbac_context.role)
    
    if not rbac.can_create_feedback():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create feedback",
        )
    
    # Convert request to internal model and add user info from headers
    feedback_data = FeedbackCreate(
        order_id=feedback_request.order_id,
        restaurant_id=feedback_request.restaurant_id,
        rating=feedback_request.rating,
        review_text=feedback_request.review_text,
        user_id=rbac_context.user_id,
        email=rbac_context.email,
    )
    
    logger.info(
        f"Creating feedback | user={rbac_context.user_id} | order={feedback_data.order_id} | restaurant={feedback_data.restaurant_id}"
    )
    return await service.create_feedback(feedback_data)


@app.get(
    "/feedbacks/restaurant/{restaurant_id}",
    response_model=FeedbackList,
    tags=["Feedback"],
)
async def get_feedbacks_for_restaurant(
    restaurant_id: str,
    rbac_context: Annotated[RBACContext, Depends(get_rbac_context)],
    service: Annotated[FeedbackService, Depends(get_feedback_service)],
) -> FeedbackList:
    """
    Get all feedbacks for a restaurant with average rating.
    
    **Access:** All authenticated users
    - Returns all non-deleted feedbacks
    - Includes average rating calculation
    """
    logger.info(
        f"Fetching feedbacks | restaurant={restaurant_id} | user={rbac_context.user_id}"
    )
    return await service.get_feedbacks_for_restaurant(restaurant_id)


@app.get(
    "/feedbacks/{feedback_id}",
    response_model=FeedbackOut,
    tags=["Feedback"],
)
async def get_feedback(
    feedback_id: str,
    rbac_context: Annotated[RBACContext, Depends(get_rbac_context)],
    service: Annotated[FeedbackService, Depends(get_feedback_service)],
) -> FeedbackOut:
    """
    Get a specific feedback by ID.
    
    **Access:** All authenticated users
    """
    feedback = await service.get_feedback_by_id(feedback_id)
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )
    
    logger.info(f"Retrieved feedback {feedback_id} | user={rbac_context.user_id}")
    return feedback


@app.put(
    "/feedbacks/{feedback_id}",
    response_model=FeedbackOut,
    tags=["Feedback"],
)
async def update_feedback(
    feedback_id: str,
    feedback_request: FeedbackUpdateRequest,
    rbac_context: Annotated[RBACContext, Depends(get_rbac_context)],
    service: Annotated[FeedbackService, Depends(get_feedback_service)],
) -> FeedbackOut:
    """
    Update feedback (rating and review text only).
    
    **Access:** CUSTOMER (only for their own feedback)
    
    - **rating**: 1-5 stars
    - **review_text**: 10-500 characters
    """
    # First get the feedback to check ownership
    existing_feedback = await service.get_feedback_by_id(feedback_id)
    
    if not existing_feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )
    
    # Check if user is the owner (RBAC: customers can only update their own feedback)
    if existing_feedback.user_id != rbac_context.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own feedback",
        )
    
    # Update the feedback
    updated = await service.update_feedback(
        feedback_id,
        feedback_request.rating,
        feedback_request.review_text,
    )
    
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to update feedback",
        )
    
    logger.info(f"Updated feedback {feedback_id} | user={rbac_context.user_id}")
    return updated


@app.delete(
    "/feedbacks/{feedback_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Feedback"],
)
async def delete_feedback(
    feedback_id: str,
    rbac_context: Annotated[RBACContext, Depends(get_rbac_context)],
    service: Annotated[FeedbackService, Depends(get_feedback_service)],
) -> None:
    """
    Delete (soft delete) a feedback.
    
    **Access:** ADMIN only
    - Marks feedback as deleted without removing from database
    - Deleted feedbacks don't appear in GET requests
    """
    rbac = RBACService(rbac_context.role)
    
    if not rbac.can_delete_feedback():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete feedback",
        )
    
    success = await service.delete_feedback(feedback_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )
    
    logger.info(f"Deleted feedback {feedback_id} | admin={rbac_context.user_id}")


# ============================================================================
# INTERNAL SERVICE ENDPOINTS (Service-to-Service)
# ============================================================================


@app.get(
    "/internal/restaurants/{restaurant_id}/average-rating",
    response_model=dict,
    tags=["Internal"],
)
async def get_average_rating_internal(
    restaurant_id: str,
    service: Annotated[FeedbackService, Depends(get_feedback_service)],
) -> dict:
    """
    Internal endpoint: Get average rating for a restaurant.
    
    **Access:** Other microservices only (no auth required).
    - Used by Restaurant Service to display ratings
    - Used by Order Service for recommendations
    """
    average_rating = await service.db.get_average_rating(restaurant_id)
    feedback_count = len(await service.db.get_feedbacks_by_restaurant(restaurant_id))
    
    return {
        "restaurant_id": restaurant_id,
        "average_rating": round(average_rating, 2),
        "feedback_count": feedback_count,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.feedback_service.main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=True,
    )
