import httpx
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.analysis import AnalysisRun, ApiChange, Impact, AnalysisStatus, ChangeType, Severity, RiskLevel
from app.models.base import AuditMixin

# Need direct DB access for manual insertion since we don't have Write APIs yet
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def verify_analysis_models():
    # 1. Setup via API (Org, Service, Specs)
    base_url = "http://127.0.0.1:8000/ruptrapi/v1"
    
    # Org
    suffix = str(uuid.uuid4())[:8]
    org_res = httpx.post(f"{base_url}/organizations/", json={"name": f"Ana Org {suffix}", "slug": f"ana-org-{suffix}"})
    org_id = org_res.json()["id"]
    
    # User (for audit)
    user_res = httpx.post(f"{base_url}/users/", json={"email": f"ana-{suffix}@ex.com", "name": "Ana User", "role": "ADMIN", "organization_id": org_id})
    user_id = user_res.json()["id"]
    
    # Service
    svc_res = httpx.post(f"{base_url}/services/", json={"name": "Ana Service", "organization_id": org_id})
    service_id = svc_res.json()["id"]
    
    # Spec 1
    s1_res = httpx.post(f"{base_url}/services/{service_id}/specs/", json={"version_label": "v1", "raw_spec": {"info": "v1"}})
    s1_id = s1_res.json()["id"]
    
    # Spec 2
    s2_res = httpx.post(f"{base_url}/services/{service_id}/specs/", json={"version_label": "v2", "raw_spec": {"info": "v2"}})
    s2_id = s2_res.json()["id"]
    
    # Consumer
    cons_res = httpx.post(f"{base_url}/consumers/", json={"name": "Ana Consumer", "organization_id": org_id})
    cons_id = cons_res.json()["id"]

    print("Setup complete. Inserting Analysis data directly...")
    
    db = SessionLocal()
    try:
        # Insert Run
        run = AnalysisRun(
            service_id=service_id,
            old_spec_id=s1_id,
            new_spec_id=s2_id,
            status=AnalysisStatus.SUCCESS,
            organization_id=org_id,
            created_by=user_id
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        print(f"Inserted Run: {run.id}")
        
        # Insert Change
        change = ApiChange(
            service_id=service_id,
            old_spec_id=s1_id,
            new_spec_id=s2_id,
            change_type=ChangeType.BREAKING,
            severity=Severity.HIGH,
            description="Something broke",
            organization_id=org_id,
            created_by=user_id
        )
        db.add(change)
        db.commit()
        db.refresh(change)
        print(f"Inserted Change: {change.id}")
        
        # Insert Impact
        impact = Impact(
            api_change_id=change.id,
            consumer_id=cons_id,
            risk_level=RiskLevel.HIGH,
            organization_id=org_id,
            created_by=user_id
        )
        db.add(impact)
        db.commit()
        db.refresh(impact)
        print(f"Inserted Impact: {impact.id}")
        
    finally:
        db.close()
        
    # Verify via API
    print("Verifying via API...")
    
    # List Runs
    res = httpx.get(f"{base_url}/analysis/runs/?service_id={service_id}")
    if len(res.json()) > 0:
        print("SUCCESS: Found Analysis Runs")
    else:
        print("ERROR: No Runs found")

    # List Changes
    res = httpx.get(f"{base_url}/analysis/changes/?service_id={service_id}")
    changes = res.json()
    if len(changes) > 0 and changes[0]["change_type"] == "BREAKING":
        print("SUCCESS: Found Api Changes")
    else:
        print("ERROR: Changes not found or incorrect")

    # List Impacts
    res = httpx.get(f"{base_url}/analysis/impacts/?consumer_id={cons_id}")
    if len(res.json()) > 0:
        print("SUCCESS: Found Impacts")
    else:
        print("ERROR: Impacts not found")

if __name__ == "__main__":
    verify_analysis_models()
