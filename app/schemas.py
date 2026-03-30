# from datetime import datetime

# from pydantic import BaseModel, EmailStr, Field


# class UserCreate(BaseModel):
#     email: EmailStr
#     password: str = Field(min_length=8, max_length=128)
#     full_name: str | None = Field(default=None, max_length=200)


# class UserOut(BaseModel):
#     id: str
#     email: EmailStr
#     full_name: str | None
#     created_at: datetime

#     model_config = {"from_attributes": True}


# class ChangePassword(BaseModel):
#     current_password: str = Field(..., description="Your current password")
#     new_password: str = Field(min_length=8, max_length=128, description="New password (min 8 chars)")


# class Token(BaseModel):
#     access_token: str
#     token_type: str = "bearer"

