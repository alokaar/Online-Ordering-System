from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MenuCategory(str, Enum):
    PIZZA = "Pizza"
    RICE = "Rice"
    NOODLES = "Noodles"
    DINNER_SPECIAL = "Dinner Special"
    BEVERAGES = "Beverages"


class MenuItemCreate(BaseModel):

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float = Field(..., gt=0)
    category: MenuCategory
    image_url: str | None = None
    is_available: bool = True


class MenuItemUpdate(BaseModel):

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float | None = Field(default=None, gt=0)
    category: MenuCategory | None = None
    image_url: str | None = None
    is_available: bool | None = None


class MenuItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    price: float
    category: str
    image_url: str | None
    is_available: bool
    created_at: datetime
