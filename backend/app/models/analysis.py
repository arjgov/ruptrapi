from sqlalchemy import Column, String, ForeignKey, Enum, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseEntity
import enum

# Enums
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

class AnalysisStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class ApiChange(BaseEntity):
    __tablename__ = "api_changes"
    
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    old_spec_id = Column(UUID(as_uuid=True), ForeignKey("api_spec_versions.id"), nullable=False)
    new_spec_id = Column(UUID(as_uuid=True), ForeignKey("api_spec_versions.id"), nullable=False)
    
    change_type = Column(Enum(ChangeType), nullable=False)
    severity = Column(Enum(Severity), nullable=False)
    http_method = Column(String, nullable=True)
    path = Column(String, nullable=True)
    description = Column(Text, nullable=False)

class Impact(BaseEntity):
    __tablename__ = "impacts"
    
    api_change_id = Column(UUID(as_uuid=True), ForeignKey("api_changes.id"), nullable=False)
    consumer_id = Column(UUID(as_uuid=True), ForeignKey("consumers.id"), nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False)

class AnalysisRun(BaseEntity):
    __tablename__ = "analysis_runs"
    
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    old_spec_id = Column(UUID(as_uuid=True), ForeignKey("api_spec_versions.id"), nullable=False)
    new_spec_id = Column(UUID(as_uuid=True), ForeignKey("api_spec_versions.id"), nullable=False)
    status = Column(Enum(AnalysisStatus), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships can be added if needed
