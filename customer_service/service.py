"""Business Logic Layer for Customer Service"""

import logging
from datetime import datetime, timezone
from typing import Annotated, Optional

from bson import ObjectId
from fastapi import Depends, HTTPException, Header, status
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorDatabase
import httpx
from pymongo.errors import DuplicateKeyError

from .config import settings
from .database import get_database
from .models import (
    CustomerCreate,
    CustomerOut,
    CustomerUpdate,
    RBACContext,
    UserRole,
)

logger = logging.getLogger(__name__)


class RBACService:
    """Role-Based Access Control Service"""

    def __init__(self, role: UserRole):
        self.role = role

    def can_view_customer(self, target_user_id: str, requester_user_id: str) -> bool:
        """
        Determine if requester can view customer profile.
        - ADMIN: can view any customer
        - CUSTOMER/RESTAURANT: can view own profile only
        """
        if self.role == UserRole.ADMIN:
            return True
        if self.role in [UserRole.CUSTOMER, UserRole.RESTAURANT]:
            return target_user_id == requester_user_id
        return False

    def can_update_customer(self, target_user_id: str, requester_user_id: str) -> bool:
        """
        Determine if requester can update customer profile.
        - ADMIN: can update any customer
        - CUSTOMER/RESTAURANT: can update own profile only
        """
        if self.role == UserRole.ADMIN:
            return True
        if self.role in [UserRole.CUSTOMER, UserRole.RESTAURANT]:
            return target_user_id == requester_user_id
        return False

    def can_delete_customer(self, target_user_id: str, requester_user_id: str) -> bool:
        """
        Determine if requester can delete customer profile.
        - ADMIN: can delete any customer
        - Others: cannot delete
        """
        return self.role == UserRole.ADMIN

    def can_list_customers(self) -> bool:
        """
        Determine if requester can list all customers.
        - ADMIN: can list all
        - Others: cannot list all
        """
        return self.role == UserRole.ADMIN


async def get_rbac_context(
    x_user_id: Annotated[str, Header()] = None,
    x_user_email: Annotated[str, Header()] = None,
    x_user_role: Annotated[str, Header()] = None,
) -> RBACContext:
    """
    Extract RBAC context from request headers (set by API Gateway).
    Headers expected: X-User-ID, X-User-Email, X-User-Role
    """
    if not all([x_user_id, x_user_email, x_user_role]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication headers from Gateway",
        )

    try:
        role = UserRole(x_user_role.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid role: {x_user_role}",
        )

    return RBACContext(user_id=x_user_id, email=x_user_email, role=role)


def require_role(*allowed_roles: UserRole):
    """
    Dependency for requiring specific roles.
    Usage: @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])
    """

    async def check_role(rbac_context: Annotated[RBACContext, Depends(get_rbac_context)]):
        if rbac_context.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{rbac_context.role}' not allowed. Required: {allowed_roles}",
            )
        return rbac_context

    return check_role


class CustomerService:
    """Customer business logic service"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.customers

    async def create_customer(self, customer_data: CustomerCreate) -> CustomerOut:
        """Create a new customer"""
        email = customer_data.email.lower().strip()

        # Ensure the user exists in Auth Service (users there always have a hashed_password),
        # otherwise the user would never be able to login.
        await self.validate_auth_user_exists_and_matches_email(
            user_id=customer_data.user_id,
            email=email,
        )

        existing_email = await self.collection.find_one({"email": email})
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered in customer profile",
            )

        existing = await self.collection.find_one({"user_id": customer_data.user_id})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer profile already exists for this user",
            )

        doc = {
            "user_id": customer_data.user_id,
            "email": email,
            "full_name": customer_data.full_name,
            "phone": customer_data.phone,
            "address": customer_data.address,
            "role": customer_data.role.value,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        try:
            result = await self.collection.insert_one(doc)
        except DuplicateKeyError as e:
            # Fallback for race conditions (indexes already enforce uniqueness).
            if "email" in str(e).lower():
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered in customer profile") from None
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Customer profile already exists for this user") from None
        
        # Verify the document was actually inserted
        created = await self.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Customer creation failed",
            )
        logger.info(f"Customer created successfully | user_id={customer_data.user_id} | role={customer_data.role} | db_id={result.inserted_id}")
        return self._doc_to_out(created)

    async def validate_auth_user_exists_and_matches_email(self, user_id: str, email: str) -> None:
        """
        Prevent creating customer profiles for non-existent Auth users (no password => cannot login).
        Also prevents email mismatches for the given user_id.
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    f"{settings.auth_service_url}/internal/users/{user_id}",
                )
        except httpx.RequestError as e:
            logger.error("Auth service unreachable while validating user: %s", e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service is unreachable",
            ) from None

        if resp.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User must be registered in Auth Service before creating a customer profile",
            )

        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to validate user in Auth Service",
            )

        data = resp.json()
        auth_email = (data.get("email") or "").lower().strip()
        if auth_email != email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email does not match the Auth user",
            )

    async def get_customer_by_user_id(self, user_id: str) -> Optional[CustomerOut]:
        """Get customer by user ID"""
        doc = await self.collection.find_one({"user_id": user_id})
        if not doc:
            return None
        return self._doc_to_out(doc)

    async def get_customer_by_id(self, customer_id: str) -> Optional[CustomerOut]:
        """Get customer by customer ID (MongoDB _id)"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(customer_id)})
            if not doc:
                return None
            return self._doc_to_out(doc)
        except Exception:
            return None

    async def list_customers(self, skip: int = 0, limit: int = 10) -> tuple[list[CustomerOut], int]:
        """List all customers with pagination"""
        cursor = self.collection.find().skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        total = await self.collection.count_documents({})
        return [self._doc_to_out(doc) for doc in docs], total

    async def update_customer(self, user_id: str, update_data: CustomerUpdate) -> Optional[CustomerOut]:
        """Update customer profile"""
        update_doc = {
            k: v for k, v in update_data.model_dump().items() if v is not None
        }
        if not update_doc:
            doc = await self.collection.find_one({"user_id": user_id})
            return self._doc_to_out(doc) if doc else None

        update_doc["updated_at"] = datetime.now(timezone.utc)

        result = await self.collection.find_one_and_update(
            {"user_id": user_id},
            {"$set": update_doc},
            return_document=True,
        )
        return self._doc_to_out(result) if result else None

    async def delete_customer(self, user_id: str) -> bool:
        """Delete customer profile"""
        result = await self.collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0

    @staticmethod
    def _doc_to_out(doc: dict) -> CustomerOut:
        """Convert MongoDB document to CustomerOut model"""
        return CustomerOut(
            id=str(doc["_id"]),
            user_id=doc["user_id"],
            email=doc["email"],
            full_name=doc.get("full_name"),
            phone=doc.get("phone"),
            address=doc.get("address"),
            role=UserRole(doc.get("role", "customer")),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
        )


async def get_customer_service(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> CustomerService:
    """Get customer service instance"""
    return CustomerService(db)
