"""Pydantic Models for Customer Service"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User Roles for RBAC"""
    ADMIN = "admin"
    RESTAURANT = "restaurant"
    CUSTOMER = "customer"
    GUEST = "guest"


class CustomerBase(BaseModel):
    """Base customer model"""
    email: EmailStr
    full_name: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=500)


class CustomerCreate(CustomerBase):
    """Customer creation model"""
    user_id: str = Field(..., description="User ID from auth service")
    role: UserRole = Field(..., description="User role (from JWT token via Gateway)")


class CustomerUpdate(BaseModel):
    """Customer update model"""
    full_name: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=500)


class CustomerOut(CustomerBase):
    """Customer output model"""
    id: str
    user_id: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerListOut(BaseModel):
    """List of customers"""
    customers: list[CustomerOut]
    total: int


class RBACContext(BaseModel):
    """RBAC Context from Gateway"""
    user_id: str
    email: str
    role: UserRole


class HealthResponse(BaseModel):
    """Health check response"""
    service: str
    status: str
    database: str


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    error_code: Optional[str] = None
