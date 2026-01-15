from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.models.organization import Organization
from app.schemas import organization as org_schemas

router = APIRouter()

@router.post("/", response_model=org_schemas.Organization)
def create_organization(organization: org_schemas.OrganizationCreate, db: Session = Depends(get_db)):
    db_org = Organization(name=organization.name, slug=organization.slug)
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org

@router.get("/", response_model=List[org_schemas.Organization])
def list_organizations(
    skip: int = 0, 
    limit: int = 100, 
    include_deleted: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(Organization)
    if not include_deleted:
        query = query.filter(Organization.is_deleted == False)
    return query.offset(skip).limit(limit).all()

@router.patch("/{id}", response_model=org_schemas.Organization)
def update_organization(id: UUID, organization_update: org_schemas.OrganizationUpdate, db: Session = Depends(get_db)):
    db_org = db.query(Organization).filter(Organization.id == id).first()
    if not db_org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    update_data = organization_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_org, key, value)

    db.commit()
    db.refresh(db_org)
    return db_org
