from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import uuid4


class MenuItemBase(BaseModel):
    name: str
    description: Optional[str] = ""
    price: float
    category: Optional[str] = "General"
    available: bool = True


class MenuItemCreate(MenuItemBase):
    pass


class MenuItem(MenuItemBase):
    id: str = Field(default_factory=lambda: str(uuid4()))


class RestaurantBase(BaseModel):
    name: str
    description: Optional[str] = ""
    address: str
    phone: str
    cuisine: str
    is_active: bool = True


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    cuisine: Optional[str] = None
    is_active: Optional[bool] = None


class Restaurant(RestaurantBase):
    id: str = Field(default_factory=lambda: str(uuid4()))
    menu: List[MenuItem] = Field(default_factory=list)