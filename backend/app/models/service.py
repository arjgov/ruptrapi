from sqlalchemy import Column, String, ForeignKey, JSON, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseEntity

class Service(BaseEntity):
    __tablename__ = "services"
    
    name = Column(String, nullable=False)
    base_path = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    specs = relationship("ApiSpecVersion", back_populates="service")

class ApiSpecVersion(BaseEntity):
    __tablename__ = "api_spec_versions"
    
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    version_label = Column(String, nullable=False) # e.g., v1.0, 2024-01-01
    raw_spec = Column(JSON, nullable=False)
    hash = Column(String, nullable=True) # To check for duplicates
    
    service = relationship("Service", back_populates="specs")
