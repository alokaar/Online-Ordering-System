from datetime import datetime

from pydantic import BaseModel, Field


class CartItem(BaseModel):
    menu_item_id: str
    name: str | None = None
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)


class CartOut(BaseModel):
    items: list[CartItem]
    total: float


class OrderCreate(BaseModel):
    delivery_address: str = Field(..., min_length=10, max_length=500)
    phone_number: str = Field(..., min_length=10, max_length=20)


class OrderOut(BaseModel):
    id: str
    user_id: str
    items: list[CartItem]
    total: float
    status: str
    delivery_address: str
    phone_number: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
