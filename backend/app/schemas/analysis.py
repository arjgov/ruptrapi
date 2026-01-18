from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum

# Enums
class ChangeType(str, Enum):
    BREAKING = "BREAKING"
    NON_BREAKING = "NON_BREAKING"

class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class RiskLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class AnalysisStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

# ApiChange
class ApiChangeBase(BaseModel):
    change_type: ChangeType
    severity: Severity
    http_method: Optional[str] = None
    path: Optional[str] = None
    description: str

class ApiChange(ApiChangeBase):
    id: UUID
    service_id: UUID
    old_spec_id: UUID
    new_spec_id: UUID
    organization_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

# Impact
class ImpactBase(BaseModel):
    risk_level: RiskLevel

class Impact(ImpactBase):
    id: UUID
    api_change_id: UUID
    consumer_id: UUID
    organization_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

# AnalysisRun
class AnalysisRunBase(BaseModel):
    service_id: UUID
    old_spec_id: Optional[UUID] = None
    new_spec_id: Optional[UUID] = None

class AnalysisRunCreate(AnalysisRunBase):
    pass

class AnalysisRun(AnalysisRunBase):
    id: UUID
    status: AnalysisStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    organization_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
