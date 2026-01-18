from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime

from app.core.database import get_db, SessionLocal
from app.models.analysis import ApiChange, Impact, AnalysisRun, AnalysisStatus, ChangeType, RiskLevel, Severity
from app.models.service import ApiSpecVersion
from app.models.consumer import ConsumerDependency
from app.core.diff_engine import DiffEngine
from app.schemas import analysis as schemas

router = APIRouter()

def process_analysis_run_task(run_id: UUID):
    """
    Background task to compute diffs and impacts.
    Creates its own DB session to ensure thread safety and persistence.
    """
    db = SessionLocal()
    try:
        run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if not run:
            return # Should not happen

        old_spec = db.query(ApiSpecVersion).filter(ApiSpecVersion.id == run.old_spec_id).first()
        new_spec = db.query(ApiSpecVersion).filter(ApiSpecVersion.id == run.new_spec_id).first()

        # Run Diff Engine
        engine = DiffEngine()
        changes_data = engine.compute_diff(old_spec.raw_spec, new_spec.raw_spec)
        
        # Save Changes and Calculate Impact
        for change_data in changes_data:
            api_change = ApiChange(
                service_id=run.service_id,
                old_spec_id=run.old_spec_id,
                new_spec_id=run.new_spec_id,
                organization_id=run.organization_id,
                change_type=change_data["change_type"],
                severity=change_data["severity"],
                http_method=change_data.get("http_method"),
                path=change_data.get("path"),
                description=change_data["description"]
            )
            db.add(api_change)
            db.flush() 
            
            if api_change.http_method and api_change.path:
                dependencies = db.query(ConsumerDependency).filter(
                    ConsumerDependency.service_id == run.service_id,
                    ConsumerDependency.path == api_change.path,
                    ConsumerDependency.http_method == api_change.http_method,
                    ConsumerDependency.is_deleted == False
                ).all()
                
                for dep in dependencies:
                    risk = RiskLevel.LOW
                    if api_change.severity == Severity.HIGH:
                        risk = RiskLevel.HIGH
                    elif api_change.severity == Severity.MEDIUM:
                        risk = RiskLevel.MEDIUM
                        
                    impact = Impact(
                        api_change_id=api_change.id,
                        consumer_id=dep.consumer_id,
                        organization_id=run.organization_id,
                        risk_level=risk
                    )
                    db.add(impact)
        
        run.status = AnalysisStatus.SUCCESS
        run.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        print(f"Analysis Job Failed: {e}") # Retrieve logger properly in production
        db.rollback()
        # Re-fetch run to update status safely
        run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if run:
            run.status = AnalysisStatus.FAILED
            db.commit()
    finally:
        db.close()

# --- Analysis Runs ---

@router.post("/runs/", response_model=schemas.AnalysisRun)
def create_analysis_run(
    run_in: schemas.AnalysisRunCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # 1. Verify existence
    old_spec = db.query(ApiSpecVersion).filter(ApiSpecVersion.id == run_in.old_spec_id).first()
    new_spec = db.query(ApiSpecVersion).filter(ApiSpecVersion.id == run_in.new_spec_id).first()
    
    if not old_spec or not new_spec:
        raise HTTPException(status_code=404, detail="One or both specs not found")
        
    if old_spec.service_id != run_in.service_id or new_spec.service_id != run_in.service_id:
        raise HTTPException(status_code=400, detail="Specs must belong to the specified service")

    # 2. Create Run Record (PENDING)
    analysis_run = AnalysisRun(
        service_id=run_in.service_id,
        old_spec_id=run_in.old_spec_id,
        new_spec_id=run_in.new_spec_id,
        status=AnalysisStatus.PENDING,
        organization_id=old_spec.organization_id,
        started_at=datetime.utcnow()
    )
    db.add(analysis_run)
    db.commit()
    db.refresh(analysis_run)
    
    # 3. Queue Background Task
    background_tasks.add_task(process_analysis_run_task, analysis_run.id)

    return analysis_run

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
