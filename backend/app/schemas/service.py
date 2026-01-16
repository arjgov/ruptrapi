from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Common
class OrganizationBase(BaseModel):
    name: str
    slug: str

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Service
# Service
class ServiceBase(BaseModel):
    name: str
    base_path: Optional[str] = None
    description: Optional[str] = None

class ServiceCreate(ServiceBase):
    organization_id: UUID

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    base_path: Optional[str] = None
    description: Optional[str] = None
    is_deleted: Optional[bool] = None

class Service(ServiceBase):
    id: UUID
    organization_id: UUID
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Spec
class SpecVersionBase(BaseModel):
    version_label: str
    raw_spec: dict

class SpecVersionCreate(SpecVersionBase):
    pass

class SpecVersion(SpecVersionBase):
    id: UUID
    service_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
