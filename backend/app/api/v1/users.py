from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID

from app.core.database import get_async_db
from app.models.user import User
from app.schemas import user as schemas

router = APIRouter()

@router.post("/", response_model=schemas.User)
async def create_user(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_async_db)):
    # Check existing by email
    result = await db.execute(select(User).filter(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Check org exists (optional in V0, but nice to have)
    # Ignored for speed, DB FK handles it
    
    user = User(**user_in.dict())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/", response_model=List[schemas.User])
async def list_users(
    organization_id: UUID = None, 
    skip: int = 0, 
    limit: int = 100, 
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_async_db)
):
    query = select(User)
    if organization_id:
        query = query.filter(User.organization_id == organization_id)
        
    if not include_deleted:
        query = query.filter(User.is_deleted == False)
        
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/by-email/{email}", response_model=schemas.User)
async def get_user_by_email(email: str, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/{user_id}", response_model=schemas.User)
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/{user_id}", response_model=schemas.User)
async def update_user(
    user_id: UUID, 
    user_in: schemas.UserUpdate, 
    db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    for field, value in user_in.dict(exclude_unset=True).items():
        setattr(user, field, value)
        
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}", response_model=schemas.User)
async def delete_user(user_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_deleted = True
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
