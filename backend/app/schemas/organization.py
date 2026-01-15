from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class OrganizationBase(BaseModel):
    name: str
    slug: str

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    is_deleted: Optional[bool] = None

class Organization(OrganizationBase):
    id: UUID
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
