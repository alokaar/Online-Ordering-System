from pydantic import BaseModel
from typing import Optional

class DeliveryCreate(BaseModel):
    order_id: str
    status: str = "Pending"
    driver_name: str
    location: str
    estimated_time: str

class DeliveryOut(BaseModel):
    id: str
    order_id: str
    status: str
    driver_name: str
    location: str
    estimated_time: str

class DeliveryUpdate(BaseModel):
    status: Optional[str] = None
    location: Optional[str] = None
    estimated_time: Optional[str] = None