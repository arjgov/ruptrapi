from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID

from app.core.database import get_async_db
from app.models.consumer import Consumer, ConsumerDependency
from app.models.service import Service
from app.schemas import consumer as schemas

router = APIRouter()

# --- Consumers ---

@router.post("/", response_model=schemas.Consumer)
async def create_consumer(consumer_in: schemas.ConsumerCreate, db: AsyncSession = Depends(get_async_db)):
    consumer = Consumer(**consumer_in.dict())
    db.add(consumer)
    await db.commit()
    await db.refresh(consumer)
    return consumer

@router.get("/", response_model=List[schemas.Consumer])
async def list_consumers(
    organization_id: UUID = None, 
    skip: int = 0, 
    limit: int = 100, 
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_async_db)
):
    query = select(Consumer)
    if organization_id:
        query = query.filter(Consumer.organization_id == organization_id)
        
    if not include_deleted:
        query = query.filter(Consumer.is_deleted == False)
        
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{consumer_id}", response_model=schemas.Consumer)
async def get_consumer(consumer_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Consumer).filter(Consumer.id == consumer_id))
    consumer = result.scalars().first()
    if not consumer:
        raise HTTPException(status_code=404, detail="Consumer not found")
    return consumer

@router.patch("/{consumer_id}", response_model=schemas.Consumer)
async def update_consumer(
    consumer_id: UUID, 
    consumer_in: schemas.ConsumerUpdate, 
    db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(select(Consumer).filter(Consumer.id == consumer_id))
    consumer = result.scalars().first()
    if not consumer:
        raise HTTPException(status_code=404, detail="Consumer not found")
        
    for field, value in consumer_in.dict(exclude_unset=True).items():
        setattr(consumer, field, value)
        
    db.add(consumer)
    await db.commit()
    await db.refresh(consumer)
    return consumer

@router.delete("/{consumer_id}", response_model=schemas.Consumer)
async def delete_consumer(consumer_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Consumer).filter(Consumer.id == consumer_id))
    consumer = result.scalars().first()
    if not consumer:
        raise HTTPException(status_code=404, detail="Consumer not found")
        
    consumer.is_deleted = True
    db.add(consumer)
    await db.commit()
    await db.refresh(consumer)
    return consumer

# --- Dependencies ---

@router.post("/{consumer_id}/dependencies/", response_model=schemas.ConsumerDependency)
async def add_dependency(
    consumer_id: UUID, 
    dep_in: schemas.ConsumerDependencyCreate, 
    db: AsyncSession = Depends(get_async_db)
):
    # 1. Verify Consumer
    result = await db.execute(select(Consumer).filter(Consumer.id == consumer_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Consumer not found")
        
    # 2. Verify Service and get name
    result = await db.execute(select(Service).filter(Service.id == dep_in.service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # 3. Check for duplicates (including soft-deleted)
    result = await db.execute(select(ConsumerDependency).filter(
        ConsumerDependency.consumer_id == consumer_id,
        ConsumerDependency.service_id == dep_in.service_id,
        ConsumerDependency.http_method == dep_in.http_method,
        ConsumerDependency.path == dep_in.path
    ))
    existing = result.scalars().first()
    
    if existing:
        if existing.is_deleted:
            # Revive
            existing.is_deleted = False
            db.add(existing)
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            raise HTTPException(status_code=409, detail="Dependency already exists")
            
    # 4. Create new
    # Fetch consumer to get org ID and name
    result = await db.execute(select(Consumer).filter(Consumer.id == consumer_id))
    consumer = result.scalars().first()
    
    dep = ConsumerDependency(
        consumer_id=consumer_id,
        consumer_name=consumer.name,
        service_id=dep_in.service_id,
        service_name=service.name,
        http_method=dep_in.http_method,
        path=dep_in.path,
        organization_id=consumer.organization_id
    )
    db.add(dep)
    await db.commit()
    await db.refresh(dep)
    return dep

@router.get("/{consumer_id}/dependencies/", response_model=List[schemas.ConsumerDependency])
async def list_dependencies(consumer_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(ConsumerDependency).filter(
        ConsumerDependency.consumer_id == consumer_id, 
        ConsumerDependency.is_deleted == False
    ))
    return result.scalars().all()

@router.delete("/{consumer_id}/dependencies/{dependency_id}", response_model=schemas.ConsumerDependency)
async def remove_dependency(
    consumer_id: UUID, 
    dependency_id: UUID, 
    db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(select(ConsumerDependency).filter(
        ConsumerDependency.id == dependency_id,
        ConsumerDependency.consumer_id == consumer_id
    ))
    dep = result.scalars().first()
    
    if not dep:
        raise HTTPException(status_code=404, detail="Dependency not found")
        
    dep.is_deleted = True
    db.add(dep)
    await db.commit()
    await db.refresh(dep)
    return dep
