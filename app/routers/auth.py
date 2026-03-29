from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.auth import create_access_token, get_current_user, hash_password, user_doc_to_out, verify_password
from app.database import get_database
from app.schemas import Token, UserCreate, UserOut

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    body: UserCreate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> UserOut:
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
    """Use **username** = your email address (OAuth2 convention)."""
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
    return current
