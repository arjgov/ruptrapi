from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    role: Optional[UserRole] = UserRole.MEMBER
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    organization_id: UUID

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_deleted: Optional[bool] = None

class User(UserBase):
    id: UUID
    organization_id: UUID
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
