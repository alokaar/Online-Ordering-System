from datetime import datetime

from pydantic import BaseModel, Field


class MenuItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=50)
    image_url: str | None = None
    is_available: bool = True


class MenuItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float | None = Field(default=None, gt=0)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    image_url: str | None = None
    is_available: bool | None = None


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
