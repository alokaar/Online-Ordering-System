from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PaymentMethod(str, Enum):
    CASH = "Cash"
    CARD = "Card"
    ONLINE = "Online"


class CartItem(BaseModel):
    menu_item_id: str
    name: str | None = None
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)


class CartOut(BaseModel):
    items: list[CartItem]
    total: float


class OrderCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=100)
    delivery_address: str = Field(..., min_length=10, max_length=500)
    phone_number: str = Field(..., min_length=10, max_length=20)
    receiver_details: str | None = Field(default=None, max_length=500)
    special_ticket_instructions: str | None = Field(default=None, max_length=500)
    payment_method: PaymentMethod = PaymentMethod.CASH


class OrderOut(BaseModel):
    id: str
    user_id: str
    items: list[CartItem]
    total: float
    status: str
    delivery_address: str
    phone_number: str
    full_name: str | None = None
    email: str | None = None
    receiver_details: str | None = None
    special_ticket_instructions: str | None = None
    payment_method: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
