import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class UUIDMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class TenantMixin:
    organization_id = Column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)

class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class BaseEntity(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __abstract__ = True

class BaseOrganizationEntity(Base, UUIDMixin, TimestampMixin):
    """
    Base class for entities that ARE the organization/tenant itself,
    so they don't need a separate organization_id column.
    """
    __abstract__ = True
