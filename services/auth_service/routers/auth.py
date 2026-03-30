"""Auth Service Routes"""
from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from ..database import get_database
from ..models import ChangePassword, Token, UserCreate, UserOut
from ..service import create_access_token, get_current_user, hash_password, user_doc_to_out, verify_password

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    body: UserCreate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> UserOut:
    """Register a new user"""
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
    return user_doc_to_out(created)


@router.post("/login", response_model=Token)
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


@router.get("/me", response_model=UserOut)
async def read_me(current: Annotated[UserOut, Depends(get_current_user)]) -> UserOut:
    """Get current authenticated user profile"""
    return current


@router.post("/change-password", status_code=status.HTTP_200_OK)
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
