from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=200)


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePassword(BaseModel):
    """Change password request"""
    current_password: str = Field(..., description="Your current password")
    new_password: str = Field(min_length=8, max_length=128, description="New password (min 8 chars)")


# Menu Item Schemas
class MenuItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=50)
    image_url: str | None = Field(default=None)
    is_available: bool = Field(default=True)


class MenuItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float | None = Field(default=None, gt=0)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    image_url: str | None = Field(default=None)
    is_available: bool | None = Field(default=None)


class MenuItemOut(BaseModel):
    id: str
    name: str
    description: str | None
    price: float
    category: str
    image_url: str | None
    is_available: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# Cart/Order Schemas
class CartItem(BaseModel):
    menu_item_id: str
    name: str | None = None  # Make name optional for backward compatibility
    quantity: int = Field(..., gt=0)
    price: float  # Price at time of adding to cart


class CartOut(BaseModel):
    items: list[CartItem]
    total: float


class OrderCreate(BaseModel):
    items: list[CartItem] = Field(..., min_items=1)
    delivery_address: str = Field(..., min_length=10, max_length=500)
    phone_number: str = Field(..., min_length=10, max_length=20)


class OrderOut(BaseModel):
    id: str
    user_id: str
    items: list[CartItem]
    total: float
    status: str  # pending, confirmed, preparing, ready, delivered, cancelled
    delivery_address: str
    phone_number: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
