from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.models.service import Service, ApiSpecVersion
from app.schemas import service as schemas

router = APIRouter()

@router.post("/", response_model=schemas.Service)
def create_service(service: schemas.ServiceCreate, db: Session = Depends(get_db)):
    db_service = Service(
        name=service.name,
        base_url=service.base_url,
        description=service.description,
        organization_id=service.organization_id # In real app, get from context
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@router.get("/", response_model=List[schemas.Service])
def list_services(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Service).offset(skip).limit(limit).all()

@router.post("/{service_id}/specs/", response_model=schemas.SpecVersion)
def upload_spec(service_id: UUID, spec: schemas.SpecVersionCreate, db: Session = Depends(get_db)):
    # Verify service exists
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    db_spec = ApiSpecVersion(
        service_id=service_id,
        version_label=spec.version_label,
        raw_spec=spec.raw_spec,
        organization_id=service.organization_id
    )
    db.add(db_spec)
    db.commit()
    db.refresh(db_spec)
    return db_spec

@router.get("/{service_id}/specs/", response_model=List[schemas.SpecVersion])
def list_specs(service_id: UUID, db: Session = Depends(get_db)):
    return db.query(ApiSpecVersion).filter(ApiSpecVersion.service_id == service_id).all()
