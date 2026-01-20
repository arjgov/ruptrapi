from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Any, Dict
from uuid import UUID
import json
import hashlib

from app.core.database import get_async_db
from app.models.service import Service, ApiSpecVersion
from app.models.organization import Organization
from app.schemas import service as schemas

router = APIRouter()

# --- Services ---

@router.post("/", response_model=schemas.Service)
async def create_service(service_in: schemas.ServiceCreate, db: AsyncSession = Depends(get_async_db)):
    # Verify organization exists
    result = await db.execute(select(Organization).filter(Organization.id == service_in.organization_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Organization not found")
        
    # Check for duplicate name in org
    result = await db.execute(select(Service).filter(
        Service.organization_id == service_in.organization_id,
        Service.name == service_in.name,
        Service.is_deleted == False
    ))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Service with this name already exists in the organization")

    service = Service(**service_in.dict())
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service

@router.get("/", response_model=List[schemas.Service])
async def list_services(
    organization_id: UUID = None, 
    skip: int = 0, 
    limit: int = 100, 
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_async_db)
):
    query = select(Service)
    if organization_id:
        query = query.filter(Service.organization_id == organization_id)
        
    if not include_deleted:
        query = query.filter(Service.is_deleted == False)
        
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{service_id}", response_model=schemas.Service)
async def get_service(service_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Service).filter(Service.id == service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@router.patch("/{service_id}", response_model=schemas.Service)
async def update_service(
    service_id: UUID, 
    service_in: schemas.ServiceUpdate, 
    db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(select(Service).filter(Service.id == service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    for field, value in service_in.dict(exclude_unset=True).items():
        setattr(service, field, value)
        
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service

@router.delete("/{service_id}", response_model=schemas.Service)
async def delete_service(service_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Service).filter(Service.id == service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    service.is_deleted = True
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service

# --- Specs ---

@router.post("/{service_id}/specs/", response_model=schemas.ApiSpecVersion)
async def upload_spec(
    service_id: UUID,  # Path param
    spec_in: schemas.ApiSpecVersionBase, # Extract fields like version_label from body
    db: AsyncSession = Depends(get_async_db)
):
    # Verify Service
    result = await db.execute(select(Service).filter(Service.id == service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    # Calculate Hash
    # Ensure consistent serialization for hash
    spec_str = json.dumps(spec_in.raw_spec, sort_keys=True)
    spec_hash = hashlib.sha256(spec_str.encode('utf-8')).hexdigest()
    
    # Check for duplicate content
    result = await db.execute(select(ApiSpecVersion).filter(
        ApiSpecVersion.service_id == service_id,
        ApiSpecVersion.spec_hash == spec_hash,
        ApiSpecVersion.is_deleted == False
    ))
    if result.scalars().first():
        # Found exact same content
        raise HTTPException(status_code=409, detail="This spec content has already been uploaded for this service")

    # Create new version
    new_spec = ApiSpecVersion(
        service_id=service_id,
        version_label=spec_in.version_label,
        raw_spec=spec_in.raw_spec,
        spec_hash=spec_hash,
        organization_id=service.organization_id # Inherit org from service
    )
    
    db.add(new_spec)
    await db.commit()
    await db.refresh(new_spec)
    return new_spec

@router.get("/{service_id}/specs/", response_model=List[schemas.ApiSpecVersion])
async def list_specs(
    service_id: UUID, 
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_async_db)
):
    # Verify service logic optional but good for 404
    result = await db.execute(select(Service).filter(Service.id == service_id))
    if not result.scalars().first():
         raise HTTPException(status_code=404, detail="Service not found")

    query = select(ApiSpecVersion).filter(ApiSpecVersion.service_id == service_id)
    if not include_deleted:
        query = query.filter(ApiSpecVersion.is_deleted == False)
        
    result = await db.execute(query.order_by(ApiSpecVersion.created_at.desc()))
    return result.scalars().all()

# --- Service Dependencies (Consumers using this service) ---

@router.get("/{service_id}/dependencies/", response_model=List[Any])
async def list_service_dependencies(
    service_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """List all consumers that depend on this service"""
    # Verify service exists
    result = await db.execute(select(Service).filter(Service.id == service_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Import ConsumerDependency
    from app.models.consumer import ConsumerDependency
    from app.schemas import consumer as consumer_schemas
    
    # Query dependencies
    query = select(ConsumerDependency).filter(
        ConsumerDependency.service_id == service_id,
        ConsumerDependency.is_deleted == False
    ).order_by(ConsumerDependency.created_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()
