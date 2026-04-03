"""Feedback Service Business Logic & RBAC"""
import httpx
import logging
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Header, status

from .config import settings
from .database import get_database, MockDatabase
from .models import FeedbackCreate, FeedbackList, FeedbackOut, RBACContext, UserRole

logger = logging.getLogger(__name__)


class FeedbackService:
    """Business logic for feedback operations"""
    
    def __init__(self, db: MockDatabase):
        self.db = db
    
    async def validate_user_exists(self, user_id: str, email: str) -> tuple[bool, str]:
        """Verify user exists in Auth Service AND email matches.
        Returns: (is_valid, error_message)
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                # Call auth service internal endpoint to verify user
                logger.info(f"Validating user {user_id} with email {email} in auth service...")
                response = await client.get(
                    f"{settings.auth_service_url}/internal/users/{user_id}",
                    headers={"X-User-Email": email}
                )
                logger.info(f"Auth service response: {response.status_code}")
                
                if response.status_code == 200:
                    # Parse response and check if email matches
                    user_data = response.json()
                    returned_email = user_data.get("email", "")
                    
                    logger.info(f"User email from DB: {returned_email}, Provided email: {email}")
                    
                    # Email must match exactly
                    if returned_email.lower() == email.lower():
                        logger.info(f"✓ User {user_id} validated successfully with matching email")
                        return (True, "")
                    else:
                        logger.warning(f"✗ Email mismatch! DB: {returned_email}, Provided: {email}")
                        return (False, f"Email mismatch. You provided: {email}, but user {user_id} is registered with: {returned_email}")
                else:
                    logger.warning(f"✗ Auth service returned {response.status_code}: {response.text}")
                    return (False, "User ID not found in the system. Please register first.")
        except Exception as e:
            logger.error(f"✗ Failed to validate user in auth service: {type(e).__name__}: {e}")
            return (False, f"Error validating user: {str(e)}")
    
    async def validate_customer_profile_exists(self, user_id: str) -> bool:
        """Verify customer profile exists in Customer Service"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                # Call customer service internal endpoint to verify customer profile
                logger.info(f"Validating customer profile {user_id} in customer service...")
                response = await client.get(
                    f"{settings.customer_service_url}/internal/customers/{user_id}"
                )
                logger.info(f"Customer service response: {response.status_code}")
                if response.status_code == 200:
                    logger.info(f"✓ Customer profile {user_id} validated successfully")
                    return True
                else:
                    logger.warning(f"✗ Customer service returned {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"✗ Failed to validate customer profile in customer service: {type(e).__name__}: {e}")
            return False
    
    async def create_feedback(self, feedback_data: FeedbackCreate) -> FeedbackOut:
        """Create new feedback for an order"""
        # Validate user exists in auth service AND email matches
        user_valid, user_error = await self.validate_user_exists(feedback_data.user_id, feedback_data.email)
        if not user_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=user_error,
            )
        
        # Validate customer profile exists in customer service
        customer_exists = await self.validate_customer_profile_exists(feedback_data.user_id)
        if not customer_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer profile not found. Please contact support.",
            )

        # If this is order-feedback, ensure the order belongs to the authenticated user.
        if feedback_data.order_id:
            await self.validate_order_ownership(feedback_data.order_id, feedback_data.user_id)

        return await self.db.create_feedback(feedback_data)

    async def validate_order_ownership(self, order_id: str, user_id: str) -> None:
        """
        Ensure only the person who owns the order can submit feedback for it.

        Note: In mock-database mode we skip this validation because IDs won't exist
        in the real Order Service.
        """
        if settings.use_mock_database:
            return

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{settings.order_service_url}/orders/{order_id}",
                    params={"user_id": user_id},
                )
        except Exception as e:
            logger.error(f"✗ Order service unreachable: {type(e).__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Order service is unreachable",
            )

        if response.status_code == 200:
            order = response.json()
            # Only allow feedback for orders that have been placed.
            if order.get("status") != "order placed":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Feedback can only be submitted after the order is placed",
                )
            return

        if response.status_code in (400, 404):
            # Order Service uses both order_id and user_id to scope ownership.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only submit feedback for your own placed orders",
            )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to validate order ownership",
        )
    
    async def get_feedbacks_for_restaurant(self, restaurant_id: str) -> FeedbackList:
        """Get all feedbacks for a restaurant with average rating"""
        feedbacks = await self.db.get_feedbacks_by_restaurant(restaurant_id)
        average_rating = await self.db.get_average_rating(restaurant_id)
        
        return FeedbackList(
            restaurant_id=restaurant_id,
            feedbacks=feedbacks,
            total=len(feedbacks),
            average_rating=average_rating,
        )
    
    async def get_feedback_by_id(self, feedback_id: str) -> Optional[FeedbackOut]:
        """Get feedback by ID"""
        return await self.db.get_feedback_by_id(feedback_id)
    
    async def delete_feedback(self, feedback_id: str) -> bool:
        """Delete feedback (soft delete)"""
        return await self.db.delete_feedback(feedback_id)
    
    async def update_feedback(self, feedback_id: str, rating: int, review_text: str) -> Optional[FeedbackOut]:
        """Update feedback rating and review text"""
        return await self.db.update_feedback(feedback_id, rating, review_text)


class RBACService:
    """Role-Based Access Control for Feedback Service"""
    
    def __init__(self, role: UserRole):
        self.role = role
    
    def can_create_feedback(self) -> bool:
        """Check if user can create feedback"""
        # Only customers can create feedback
        return self.role == UserRole.CUSTOMER
    
    def can_delete_feedback(self) -> bool:
        """Check if user can delete feedback"""
        # Only admins can delete feedback
        return self.role == UserRole.ADMIN
    
    def can_view_all_feedbacks(self) -> bool:
        """Check if user can view all feedbacks"""
        # Admins and restaurants can view all, customers can view any restaurant's
        return self.role in [UserRole.ADMIN, UserRole.RESTAURANT]


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


async def get_rbac_context(
    x_user_id: Annotated[Optional[str], Header()] = None,
    x_user_email: Annotated[Optional[str], Header()] = None,
    x_user_role: Annotated[Optional[str], Header()] = None,
) -> RBACContext:
    """
    Extract RBAC context from request headers (set by API Gateway).
    Headers: X-User-ID, X-User-Email, X-User-Role
    """
    if not x_user_id or not x_user_email or not x_user_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication headers from Gateway",
        )
    
    try:
        role = UserRole(x_user_role.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {x_user_role}",
        )
    
    return RBACContext(
        user_id=x_user_id,
        email=x_user_email,
        role=role,
    )


async def get_feedback_service(
    db: Annotated[MockDatabase, Depends(get_database)]
) -> FeedbackService:
    """Dependency for feedback service"""
    return FeedbackService(db)
