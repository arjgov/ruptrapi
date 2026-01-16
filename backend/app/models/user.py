from sqlalchemy import Column, String, Boolean, Enum
from app.models.base import BaseEntity
import enum

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"

class User(BaseEntity):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True) # Changed from full_name to name per LLD
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    
    # organization_id inherited from BaseEntity -> TenantMixin
