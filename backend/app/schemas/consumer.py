from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Dependency
class ConsumerDependencyBase(BaseModel):
    service_id: UUID
    http_method: str
    path: str

class ConsumerDependencyCreate(ConsumerDependencyBase):
    pass

class ConsumerDependency(ConsumerDependencyBase):
    id: UUID
    consumer_id: UUID
    organization_id: UUID
    is_deleted: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Consumer
class ConsumerBase(BaseModel):
    name: str
    description: Optional[str] = None

class ConsumerCreate(ConsumerBase):
    organization_id: UUID

class ConsumerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_deleted: Optional[bool] = None

class Consumer(ConsumerBase):
    id: UUID
    organization_id: UUID
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    
    # Optional nested list, but usually fetched separately
    # dependencies: List[ConsumerDependency] = [] 

    class Config:
        from_attributes = True
