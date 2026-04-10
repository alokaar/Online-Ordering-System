"""Auth Service Microservice — Main Entry Point
Handles User Authentication, Registration, and Password Management
Runs on Port 8000
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Annotated

import httpx
from bson import ObjectId
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from .config import settings
from .database import get_database, is_database_connected, lifespan
from .models import ChangePassword, HealthResponse, Token, UserCreate, UserOut
from .service import create_access_token, get_current_user, hash_password, user_doc_to_out, verify_password

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app with lifespan
app = FastAPI(
    title="Auth Service",
    description="Microservice for user authentication, registration, and password management with JWT",
    version="0.1.0",
    lifespan=lifespan,
)


# ============================================================================
# INTERNAL HELPER FUNCTIONS
# ============================================================================


async def create_customer_profile_async(user_id: str, email: str, full_name: str | None) -> bool:
    """
    Try to create a customer profile in the customer service with retries.
    Returns True if successful, False if customer service remains unavailable.
    """
    profile_data = {
        "user_id": user_id,
        "email": email,
        "full_name": full_name,
        "role": "customer",
    }
    url = f"{settings.customer_service_url.rstrip('/')}/customers"
    
    for attempt in range(1, 4):  # 3 attempts
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    url,
                    json=profile_data,
                    headers={
                        "X-User-ID": user_id,
                        "X-User-Email": email,
                        "X-User-Role": "customer",
                    }
                )
                
                if response.status_code == 201:
                    logger.info(f"Customer profile created for user {user_id}")
                    return True
                elif response.status_code == 409:
                    logger.warning(f"Customer profile already exists to sync or duplicate email: {response.text}")
                    return True  # Stop retrying on conflict
                else:
                    logger.warning(f"Attempt {attempt}: Failed to create customer profile: {response.status_code} - {response.text}")
                    
        except httpx.RequestError as e:
            logger.warning(f"Attempt {attempt}: Could not connect to customer service {url} - {e}")
            
        if attempt < 3:
            await asyncio.sleep(2 ** attempt)  # Backoff: 2s, 4s
            
    logger.error(f"Failed to create customer profile for {user_id} after retries.")
    return False


# ============================================================================
# HEALTH & SYSTEM ENDPOINTS
# ============================================================================


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Check service and database health"""
    return HealthResponse(
        status="ok",
        database="connected" if is_database_connected() else "disconnected",
    )


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    """Service information"""
    return {
        "message": "Auth Service — use /docs for Swagger UI",
        "version": "0.1.0",
        "service": settings.service_name,
    }


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================


@app.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register(
    body: UserCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> UserOut:
    """Register a new user and create customer profile"""
    email = body.email.lower().strip()
    doc = {
        "email": email,
        "hashed_password": hash_password(body.password),
        "full_name": body.full_name,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = await db.users.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered") from None
    
    created = await db.users.find_one({"_id": result.inserted_id})
    if created is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User creation failed")
    
    # Try to create customer profile in the background with retries
    user_id = str(result.inserted_id)
    background_tasks.add_task(create_customer_profile_async, user_id, email, body.full_name)
    
    return user_doc_to_out(created)


@app.post("/auth/login", response_model=Token, tags=["Auth"])
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> Token:
    """Login user and return JWT token. Use **username** = your email address (OAuth2 convention)."""
    email = form_data.username.lower().strip()
    user = await db.users.find_one({"email": email})
    if user is None or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(str(user["_id"])))


@app.get("/auth/me", response_model=UserOut, tags=["Auth"])
async def read_me(current: Annotated[UserOut, Depends(get_current_user)]) -> UserOut:
    """Get current authenticated user profile"""
    return current


@app.post("/auth/change-password", status_code=status.HTTP_200_OK, tags=["Auth"])
async def change_password(
    body: ChangePassword,
    current_user: Annotated[UserOut, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> dict[str, str]:
    """Change password for authenticated user.
    
    Required: current_password (to verify user), new_password (min 8 chars)
    Returns: success message
    """
    # Get full user document with password hash
    user_doc = await db.users.find_one({"_id": ObjectId(current_user.id)})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Verify current password
    if not verify_password(body.current_password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    # Ensure new password is different from current
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Hash and update new password
    new_hashed_password = hash_password(body.new_password)
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"hashed_password": new_hashed_password}},
    )

    return {"message": "Password changed successfully"}


# ============================================================================
# INTERNAL SERVICE ENDPOINTS (Service-to-Service)
# ============================================================================


@app.get("/internal/users/{user_id}", tags=["Internal"])
async def check_user_exists(user_id: str, db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]) -> dict:
    """
    Internal endpoint: Check if user exists by ID.
    
    **Access:** Other microservices only (no auth required).
    - Used by Feedback Service to validate user before accepting feedback
    - Used by Order Service to verify customer exists
    
    Returns 200 if user exists, 404 if not.
    """
    logger.info(f"Checking if user {user_id} exists...")
    
    try:
        # Try to convert to ObjectId and query
        obj_id = ObjectId(user_id)
        logger.info(f"Converted user_id to ObjectId: {obj_id}")
        
        user = await db.users.find_one({"_id": obj_id})
        
        if user:
            logger.info(f"✓ User {user_id} found in database")
            return {
                "user_id": str(user["_id"]),
                "email": user["email"],
                "exists": True,
            }
        else:
            logger.warning(f"✗ User {user_id} not found in database")
    except Exception as e:
        logger.error(f"✗ Error checking user {user_id}: {type(e).__name__}: {e}")
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )
