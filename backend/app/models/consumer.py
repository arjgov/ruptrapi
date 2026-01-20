from sqlalchemy import Column, String, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseEntity

class Consumer(BaseEntity):
    __tablename__ = "consumers"
    
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    dependencies = relationship("ConsumerDependency", back_populates="consumer")

class ConsumerDependency(BaseEntity):
    __tablename__ = "consumer_dependencies"
    
    consumer_id = Column(UUID(as_uuid=True), ForeignKey("consumers.id"), nullable=False)
    consumer_name = Column(String, nullable=False)  # Denormalized for faster listing
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    service_name = Column(String, nullable=False)  # Denormalized for faster listing
    http_method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    
    consumer = relationship("Consumer", back_populates="dependencies")
    
    __table_args__ = (
        UniqueConstraint('consumer_id', 'service_id', 'http_method', 'path', name='uq_consumer_dep'),
    )
