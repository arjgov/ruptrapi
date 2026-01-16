from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.models.consumer import Consumer, ConsumerDependency
from app.models.organization import Organization
from app.models.service import Service
from app.schemas import consumer as schemas

router = APIRouter()

# --- Consumer CRUD ---

@router.post("/", response_model=schemas.Consumer)
def create_consumer(consumer: schemas.ConsumerCreate, db: Session = Depends(get_db)):
    # Verify organization exists
    org = db.query(Organization).filter(Organization.id == consumer.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    db_consumer = Consumer(
        name=consumer.name,
        description=consumer.description,
        organization_id=consumer.organization_id
    )
    db.add(db_consumer)
    db.commit()
    db.refresh(db_consumer)
    return db_consumer

@router.get("/", response_model=List[schemas.Consumer])
def list_consumers(
    skip: int = 0, 
    limit: int = 100, 
    organization_id: UUID = None,
    include_deleted: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(Consumer)
    
    if organization_id:
        query = query.filter(Consumer.organization_id == organization_id)
        
    if not include_deleted:
        query = query.filter(Consumer.is_deleted == False)
        
    return query.offset(skip).limit(limit).all()

@router.get("/{id}", response_model=schemas.Consumer)
def get_consumer(id: UUID, db: Session = Depends(get_db)):
    db_consumer = db.query(Consumer).filter(Consumer.id == id).first()
    if not db_consumer:
        raise HTTPException(status_code=404, detail="Consumer not found")
    return db_consumer

@router.patch("/{id}", response_model=schemas.Consumer)
def update_consumer(id: UUID, consumer_update: schemas.ConsumerUpdate, db: Session = Depends(get_db)):
    db_consumer = db.query(Consumer).filter(Consumer.id == id).first()
    if not db_consumer:
        raise HTTPException(status_code=404, detail="Consumer not found")
    
    update_data = consumer_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_consumer, key, value)
        
    db.commit()
    db.refresh(db_consumer)
    return db_consumer

# --- Dependency Management ---

@router.post("/{consumer_id}/dependencies/", response_model=schemas.ConsumerDependency)
def add_dependency(consumer_id: UUID, dep: schemas.ConsumerDependencyCreate, db: Session = Depends(get_db)):
    # Verify consumer
    consumer = db.query(Consumer).filter(Consumer.id == consumer_id).first()
    if not consumer:
        raise HTTPException(status_code=404, detail="Consumer not found")
        
    # Verify service
    service = db.query(Service).filter(Service.id == dep.service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # Check existence (including soft-deleted? If soft-deleted, we might want to revive it or create new)
    # Unique constraint will fail if we duplicate.
    # Let's check first.
    existing = db.query(ConsumerDependency).filter(
        ConsumerDependency.consumer_id == consumer_id,
        ConsumerDependency.service_id == dep.service_id,
        ConsumerDependency.http_method == dep.http_method,
        ConsumerDependency.path == dep.path
    ).first()
    
    if existing:
        if existing.is_deleted:
            # Revive
            existing.is_deleted = False
            db.commit()
            db.refresh(existing)
            return existing
        else:
            raise HTTPException(status_code=409, detail="Dependency already exists")

    db_dep = ConsumerDependency(
        consumer_id=consumer_id,
        service_id=dep.service_id,
        http_method=dep.http_method,
        path=dep.path,
        organization_id=consumer.organization_id
    )
    db.add(db_dep)
    db.commit()
    db.refresh(db_dep)
    return db_dep

@router.get("/{consumer_id}/dependencies/", response_model=List[schemas.ConsumerDependency])
def list_dependencies(consumer_id: UUID, db: Session = Depends(get_db)):
    return db.query(ConsumerDependency).filter(
        ConsumerDependency.consumer_id == consumer_id,
        ConsumerDependency.is_deleted == False
    ).all()

@router.delete("/{consumer_id}/dependencies/{dep_id}", response_model=schemas.ConsumerDependency)
def remove_dependency(consumer_id: UUID, dep_id: UUID, db: Session = Depends(get_db)):
    dep = db.query(ConsumerDependency).filter(
        ConsumerDependency.id == dep_id,
        ConsumerDependency.consumer_id == consumer_id
    ).first()
    
    if not dep:
        raise HTTPException(status_code=404, detail="Dependency not found")
        
    dep.is_deleted = True
    db.commit()
    db.refresh(dep)
    return dep
