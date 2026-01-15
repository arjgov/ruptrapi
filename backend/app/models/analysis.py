from sqlalchemy import Column, String, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseEntity
import enum

class ChangeType(str, enum.Enum):
    BREAKING = "BREAKING"
    NON_BREAKING = "NON_BREAKING"

class Severity(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class RiskLevel(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ApiChange(BaseEntity):
    __tablename__ = "api_changes"
    
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    old_spec_id = Column(UUID(as_uuid=True), ForeignKey("api_spec_versions.id"), nullable=False)
    new_spec_id = Column(UUID(as_uuid=True), ForeignKey("api_spec_versions.id"), nullable=False)
    
    change_type = Column(String, nullable=False) # Store enum as string
    severity = Column(String, nullable=False)
    http_method = Column(String, nullable=True)
    path = Column(String, nullable=True)
    description = Column(String, nullable=False)

class Impact(BaseEntity):
    __tablename__ = "impacts"
    
    change_id = Column(UUID(as_uuid=True), ForeignKey("api_changes.id"), nullable=False)
    consumer_id = Column(UUID(as_uuid=True), ForeignKey("consumers.id"), nullable=False)
    risk_level = Column(String, nullable=False)
    
    # Relationships can be added if needed
