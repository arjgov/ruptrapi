from sqlalchemy import Column, String, Boolean
from app.models.base import BaseOrganizationEntity

class Organization(BaseOrganizationEntity):
    __tablename__ = "organizations"
    
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
