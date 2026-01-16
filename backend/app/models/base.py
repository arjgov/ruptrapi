import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String, ForeignKey, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class UUIDMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class TenantMixin:
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class AuditMixin:
    is_deleted = Column(Boolean, default=False, nullable=False, server_default=text('false'))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

class BaseEntity(Base, UUIDMixin, TimestampMixin, TenantMixin, AuditMixin):
    __abstract__ = True

class BaseOrganizationEntity(Base, UUIDMixin, TimestampMixin, AuditMixin):
    """
    Base class for entities that ARE the organization/tenant itself,
    so they don't need a separate organization_id column.
    """
    __abstract__ = True
