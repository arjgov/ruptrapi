from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.models.analysis import ApiChange, Impact, AnalysisRun
from app.schemas import analysis as schemas

router = APIRouter()

# --- Analysis Runs ---

@router.get("/runs/", response_model=List[schemas.AnalysisRun])
def list_analysis_runs(
    service_id: UUID = None, 
    limit: int = 20, 
    db: Session = Depends(get_db)
):
    query = db.query(AnalysisRun)
    if service_id:
        query = query.filter(AnalysisRun.service_id == service_id)
    return query.order_by(AnalysisRun.created_at.desc()).limit(limit).all()

@router.get("/runs/{id}", response_model=schemas.AnalysisRun)
def get_analysis_run(id: UUID, db: Session = Depends(get_db)):
    run = db.query(AnalysisRun).filter(AnalysisRun.id == id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis Run not found")
    return run

# --- API Changes ---

@router.get("/changes/", response_model=List[schemas.ApiChange])
def list_api_changes(
    service_id: UUID = None,
    old_spec_id: UUID = None,
    new_spec_id: UUID = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(ApiChange)
    if service_id:
        query = query.filter(ApiChange.service_id == service_id)
    if old_spec_id:
        query = query.filter(ApiChange.old_spec_id == old_spec_id)
    if new_spec_id:
        query = query.filter(ApiChange.new_spec_id == new_spec_id)
        
    return query.limit(limit).all()

# --- Impacts ---

@router.get("/impacts/", response_model=List[schemas.Impact])
def list_impacts(
    consumer_id: UUID = None,
    api_change_id: UUID = None,
    db: Session = Depends(get_db)
):
    query = db.query(Impact)
    if consumer_id:
        query = query.filter(Impact.consumer_id == consumer_id)
    if api_change_id:
        query = query.filter(Impact.api_change_id == api_change_id)
        
    return query.all()
