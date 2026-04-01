from pydantic import BaseModel
from typing import Optional

# Model - Create new delivery
class CreateDelivery(BaseModel):
    order_id: str
    user_id: str 
    location: str
    estimated_time: str

# Model - Driver Details
class Driver(BaseModel):
    name: str
    phone: str
    vehicle_no: str
    vehicle_type: str

# Model - Output
class DeliveryOut(BaseModel):
    id: str
    order_id: str
    user_id: str
    status: str
    location: str
    estimated_time: str

    full_name: Optional[str]
    phone_number: Optional[str]
    delivery_address: Optional[str]
    total: Optional[float]
    payment_method: Optional[str]
    receiver_details: Optional[str]

    driver_name: str
    driver_phone: str
    vehicle_no: str
    vehicle_type: str

    created_at: str
    updated_at: str

# Model - Update delivery
class DeliveryUpdate(BaseModel):
    status: str | None= None
    location: str | None= None
    estimated_time: str | None= None