from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar('T')

class Page(BaseModel, Generic[T]):
    """Standard pagination response"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
    class Config:
        from_attributes = True
