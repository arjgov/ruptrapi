from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import json
import hashlib

from app.core.database import get_db
from app.models.service import Service, ApiSpecVersion
from app.models.organization import Organization
from app.schemas import service as schemas

router = APIRouter()

@router.post("/", response_model=schemas.Service)
def create_service(service: schemas.ServiceCreate, db: Session = Depends(get_db)):
    # Verify organization exists
    org = db.query(Organization).filter(Organization.id == service.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check name uniqueness within organization
    existing = db.query(Service).filter(
        Service.organization_id == service.organization_id,
        Service.name == service.name
    ).first()
    if existing:
         raise HTTPException(status_code=400, detail="Service with this name already exists in the organization")

    db_service = Service(
        name=service.name,
        base_path=service.base_path,
        description=service.description,
        organization_id=service.organization_id
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@router.get("/", response_model=List[schemas.Service])
def list_services(
    skip: int = 0, 
    limit: int = 100, 
    organization_id: UUID = None,
    include_deleted: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(Service)
    
    if organization_id:
        query = query.filter(Service.organization_id == organization_id)
        
    if not include_deleted:
        query = query.filter(Service.is_deleted == False)
        
    return query.offset(skip).limit(limit).all()

@router.get("/{id}", response_model=schemas.Service)
def get_service(id: UUID, db: Session = Depends(get_db)):
    db_service = db.query(Service).filter(Service.id == id).first()
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    return db_service

@router.patch("/{id}", response_model=schemas.Service)
def update_service(id: UUID, service_update: schemas.ServiceUpdate, db: Session = Depends(get_db)):
    db_service = db.query(Service).filter(Service.id == id).first()
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    update_data = service_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_service, key, value)
    
    db.commit()
    db.refresh(db_service)
    return db_service

# Spec endpoints (keeping existing one for now, though it should probably be moved or refactored later)
@router.post("/{service_id}/specs/", response_model=schemas.SpecVersion)
def upload_spec(service_id: UUID, spec: schemas.SpecVersionCreate, db: Session = Depends(get_db)):
    # Verify service exists
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Calculate hash
    # Ensure consistent serialization for hashing
    spec_str = json.dumps(spec.raw_spec, sort_keys=True)
    spec_hash = hashlib.sha256(spec_str.encode("utf-8")).hexdigest()

    # Check for duplicate hash in this service
    existing = db.query(ApiSpecVersion).filter(
        ApiSpecVersion.service_id == service_id,
        ApiSpecVersion.spec_hash == spec_hash
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="This spec version has already been uploaded for this service")

    db_spec = ApiSpecVersion(
        service_id=service_id,
        version_label=spec.version_label,
        raw_spec=spec.raw_spec,
        spec_hash=spec_hash,
        organization_id=service.organization_id
    )
    db.add(db_spec)
    db.commit()
    db.refresh(db_spec)
    return db_spec

@router.get("/{service_id}/specs/", response_model=List[schemas.SpecVersion])
def list_specs(service_id: UUID, db: Session = Depends(get_db)):
    # Verify service exists (optional but good practice)
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    return db.query(ApiSpecVersion).filter(
        ApiSpecVersion.service_id == service_id,
        ApiSpecVersion.is_deleted == False
    ).all()
