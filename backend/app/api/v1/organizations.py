from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID

from app.core.database import get_async_db
from app.models.organization import Organization
from app.schemas import organization as schemas

router = APIRouter()

@router.post("/", response_model=schemas.Organization)
async def create_organization(org_in: schemas.OrganizationCreate, db: AsyncSession = Depends(get_async_db)):
    # Check for existing
    result = await db.execute(select(Organization).filter(Organization.slug == org_in.slug))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Organization slug already registered")
        
    organization = Organization(**org_in.dict())
    db.add(organization)
    await db.commit()
    await db.refresh(organization)
    return organization

@router.get("/", response_model=List[schemas.Organization])
async def list_organizations(
    skip: int = 0, 
    limit: int = 100, 
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_async_db)
):
    query = select(Organization).offset(skip).limit(limit)
    if not include_deleted:
        query = query.filter(Organization.is_deleted == False)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{organization_id}", response_model=schemas.Organization)
async def get_organization(organization_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    organization = result.scalars().first()
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization

@router.patch("/{organization_id}", response_model=schemas.Organization)
async def update_organization(
    organization_id: UUID, 
    org_in: schemas.OrganizationUpdate, 
    db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    organization = result.scalars().first()
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    for field, value in org_in.dict(exclude_unset=True).items():
        setattr(organization, field, value)
        
    db.add(organization)
    await db.commit()
    await db.refresh(organization)
    return organization

@router.delete("/{organization_id}", response_model=schemas.Organization)
async def delete_organization(organization_id: UUID, db: AsyncSession = Depends(get_async_db)):
    # Soft delete
    result = await db.execute(select(Organization).filter(Organization.id == organization_id))
    organization = result.scalars().first()
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    # Check for logic constraints (e.g. has active services) if needed
    # For now, just soft delete
    organization.is_deleted = True
    db.add(organization)
    await db.commit()
    await db.refresh(organization)
    return organization
