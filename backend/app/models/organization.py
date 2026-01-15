from sqlalchemy import Column, String
from app.models.base import BaseEntity

class Organization(BaseEntity):
    __tablename__ = "organizations"
    
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
