from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from app.core.database import get_async_db, AsyncSessionLocal
from app.models.analysis import AnalysisRun, ApiChange, Impact, AnalysisStatus, ChangeType, Severity, RiskLevel
from app.models.service import ApiSpecVersion, Service
from app.models.consumer import ConsumerDependency, Consumer
from app.schemas import analysis as schemas
from app.core.diff_engine import DiffEngine

router = APIRouter()

# --- Background Task Worker ---

async def process_analysis_run_task(
    run_id: UUID, 
    old_spec_id: UUID, 
    new_spec_id: UUID
):
    """
    Async Background worker to perform diff and impact analysis.
    Uses its own AsyncSession to ensure thread/task safety.
    """
    print(f"Worker: Starting Analysis Run {run_id}")
    async with AsyncSessionLocal() as db:
        try:
            # 1. Fetch Specs
            # Use separate queries or aliases? ORM is fine here.
            stmt = select(ApiSpecVersion).where(ApiSpecVersion.id.in_([old_spec_id, new_spec_id]))
            result = await db.execute(stmt)
            specs = {s.id: s for s in result.scalars().all()}
            
            old_spec = specs.get(old_spec_id)
            new_spec = specs.get(new_spec_id)
            
            if not old_spec or not new_spec:
                print(f"Worker: Specs not found for run {run_id}")
                await _mark_run_failed(db, run_id, "One or both specs not found")
                return

            # 2. Perform Diff (CPU Bound - Run in Executor to avoid blocking event loop)
            # We create a wrapper to run the synchronous DiffEngine
            loop = asyncio.get_running_loop()
            
            def run_diff():
                engine = DiffEngine()
                return engine.compute_diff(old_spec.raw_spec, new_spec.raw_spec)

            changes_detected = await loop.run_in_executor(None, run_diff)
            
            print(f"Worker: Detected {len(changes_detected)} changes")

            # 3. Process Changes and Calculate Impact (IO Bound - Async DB)
            has_breaking = False
            total_impacts = 0

            for change_dict in changes_detected:
                # Create ApiChange record
                change = ApiChange(
                    analysis_run_id=run_id,
                    service_id=new_spec.service_id,
                    old_spec_id=old_spec.id,
                    new_spec_id=new_spec.id,
                    organization_id=new_spec.organization_id,
                    change_type=change_dict["change_type"],
                    severity=change_dict["severity"],
                    http_method=change_dict.get("http_method"), 
                    path=change_dict.get("path"),
                    description=change_dict.get("description")
                )
                db.add(change)
                # Need ID for Impact fk, but flushing in loop is ok for batch of this size
                await db.flush() 
                await db.refresh(change)

                if change.severity == Severity.HIGH:
                    has_breaking = True

                # Impact Analysis
                # Find consumers using this endpoint (Service -> Dependency)
                service_id = new_spec.service_id
                
                if change.path:
                    # If http_method is specified, filter by it. 
                    # If it's None (Path removal), find ALL dependencies on this path.
                    stmt_deps = select(ConsumerDependency).where(
                        ConsumerDependency.service_id == service_id,
                        ConsumerDependency.path == change.path,
                        ConsumerDependency.is_deleted == False
                    )
                    if change.http_method:
                        # Case-insensitive comparison (deps stored as lowercase, changes as uppercase)
                        stmt_deps = stmt_deps.where(
                            func.upper(ConsumerDependency.http_method) == change.http_method.upper()
                        )
                    
                    result_deps = await db.execute(stmt_deps)
                    dependencies = result_deps.scalars().all()
                    
                    for dep in dependencies:
                        # Determine Risk
                        risk = RiskLevel.HIGH if change.severity == Severity.HIGH else RiskLevel.LOW
                        
                        impact = Impact(
                            analysis_run_id=run_id,
                            api_change_id=change.id,
                            consumer_id=dep.consumer_id,
                            consumer_name=dep.consumer_name,
                            organization_id=new_spec.organization_id,
                            risk_level=risk
                        )
                        db.add(impact)
                        total_impacts += 1

            # 4. Finalize Run
            stmt_run = select(AnalysisRun).where(AnalysisRun.id == run_id)
            result_run = await db.execute(stmt_run)
            run = result_run.scalars().first()
            
            if run:
                run.status = AnalysisStatus.SUCCESS
                run.result_summary = f"Detected {len(changes_detected)} changes, {total_impacts} impacted consumers."
                
                db.add(run)
                await db.commit()
                print(f"Worker: Run {run_id} completed successfully.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Worker: Error processing run {run_id}: {e}")
            await db.rollback()
            await _mark_run_failed(db, run_id, str(e))

async def _mark_run_failed(db, run_id, error_msg):
    try:
        stmt = select(AnalysisRun).where(AnalysisRun.id == run_id)
        result = await db.execute(stmt)
        run = result.scalars().first()
        if run:
            run.status = AnalysisStatus.FAILED
            run.result_summary = f"Error: {error_msg}"
            db.add(run)
            await db.commit()
    except Exception as e:
        print(f"Worker: Critical failure marking run failed: {e}")


# --- API Endpoints ---

@router.post("/runs/", response_model=schemas.AnalysisRun)
async def trigger_analysis_run(
    run_in: schemas.AnalysisRunCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Trigger a new analysis execution.
    1. Basic validation.
    2. Create PENDING AnalysisRun.
    3. Dispatch Background Task.
    4. Return Run immediately.
    """
    # Validate or Auto-Select Specs
    old_id = run_in.old_spec_id
    new_id = run_in.new_spec_id
    
    if not old_id or not new_id:
        # Fetch latest 2 specs for the service
        # We need them ordered by created_at desc
        stmt_latest = select(ApiSpecVersion).where(
            ApiSpecVersion.service_id == run_in.service_id, 
            ApiSpecVersion.is_deleted == False
        ).order_by(ApiSpecVersion.created_at.desc()).limit(2)
        
        result_latest = await db.execute(stmt_latest)
        latest_specs = result_latest.scalars().all()
        
        if len(latest_specs) < 2:
            raise HTTPException(status_code=400, detail="Not enough specs versioned for this service to perform automatic comparison. Please provide specific spec IDs or upload at least 2 specs.")
            
        # latest_specs[0] is the NEWEST (limit 2 desc)
        # latest_specs[1] is the OLDER one
        new_id = latest_specs[0].id
        old_id = latest_specs[1].id

    # Verify Existence (if IDs were passed manually, or double-check auto-fetched)
    stmt = select(ApiSpecVersion).where(ApiSpecVersion.id.in_([old_id, new_id]))
    result = await db.execute(stmt)
    specs = result.scalars().all()
    
    if len(specs) != 2:
        raise HTTPException(status_code=404, detail="One or both spec versions not found")
        
    # Ensure they belong to the requested service
    if specs[0].service_id != run_in.service_id: 
         raise HTTPException(status_code=400, detail="Specs do not belong to the specified service")
    
    # Fetch service name for denormalization
    stmt_svc = select(Service).where(Service.id == run_in.service_id)
    result_svc = await db.execute(stmt_svc)
    service = result_svc.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # Create Run Record
    new_run = AnalysisRun(
        service_id=specs[0].service_id,
        service_name=service.name,
        old_spec_id=old_id,
        new_spec_id=new_id,
        status=AnalysisStatus.PENDING,
        organization_id=specs[0].organization_id,
        started_at=datetime.utcnow()
    )
    db.add(new_run)
    await db.commit()
    await db.refresh(new_run)

    # Dispatch Background Task
    # Note: background_tasks.add_task works with async functions too.
    background_tasks.add_task(
        process_analysis_run_task, 
        new_run.id, 
        old_id, 
        new_id
    )

    return new_run

@router.get("/runs/")
async def list_analysis_runs(
    service_id: UUID = None, 
    page: int = 1, 
    size: int = 20, 
    db: AsyncSession = Depends(get_async_db)
):
    """List analysis runs with pagination"""
    # Build query
    query = select(AnalysisRun)
    if service_id:
        query = query.filter(AnalysisRun.service_id == service_id)
    
    # Get total count
    count_query = select(func.count()).select_from(AnalysisRun)
    if service_id:
        count_query = count_query.filter(AnalysisRun.service_id == service_id)
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Get paginated items
    offset = (page - 1) * size
    query = query.order_by(AnalysisRun.created_at.desc()).offset(offset).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Convert to schemas
    from app.schemas import analysis as schemas
    items_schemas = [schemas.AnalysisRun.from_orm(item) for item in items]
    
    return {
        "items": items_schemas,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }

@router.get("/runs/{run_id}", response_model=schemas.AnalysisRun)
async def get_analysis_run(run_id: UUID, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(AnalysisRun).where(AnalysisRun.id == run_id))
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")
    return run

@router.get("/changes/", response_model=List[schemas.ApiChange])
async def list_api_changes(
    analysis_run_id: UUID, 
    db: AsyncSession = Depends(get_async_db)
):
    # Verify run exists
    result = await db.execute(select(AnalysisRun).where(AnalysisRun.id == analysis_run_id))
    run = result.scalars().first()
    if not run:
         raise HTTPException(status_code=404, detail="Analysis run not found")
         
    # Query changes directly by analysis_run_id (fixes duplication bug)
    query = select(ApiChange).where(ApiChange.analysis_run_id == analysis_run_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/impacts/", response_model=List[schemas.Impact])
async def list_impacts(
    analysis_run_id: UUID = None, 
    api_change_id: UUID = None,
    db: AsyncSession = Depends(get_async_db)
):
    """List impacts, optionally filtered by analysis_run_id or api_change_id"""
    query = select(Impact)
    
    if api_change_id:
        query = query.filter(Impact.api_change_id == api_change_id)
    elif analysis_run_id:
        # Now we have analysis_run_id in Impact table, so direct filter
        query = query.filter(Impact.analysis_run_id == analysis_run_id)
        
    result = await db.execute(query)
    return result.scalars().all()
