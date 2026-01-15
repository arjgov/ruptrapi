from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseEntity

class Consumer(BaseEntity):
    __tablename__ = "consumers"
    
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    dependencies = relationship("ConsumerDependency", back_populates="consumer")

class ConsumerDependency(BaseEntity):
    __tablename__ = "consumer_dependencies"
    
    consumer_id = Column(UUID(as_uuid=True), ForeignKey("consumers.id"), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    http_method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    
    consumer = relationship("Consumer", back_populates="dependencies")
    # service = relationship("Service") # Optional: relation to service
