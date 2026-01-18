import httpx
import uuid
import sys
import time

BASE_URL = "http://127.0.0.1:8000/ruptrapi/v1"

def test_analysis_flow():
    # 1. Setup Org
    suffix = str(uuid.uuid4())[:8]
    print(f"Setting up test environment (Suffix: {suffix})...")
    
    org_res = httpx.post(f"{BASE_URL}/organizations/", json={"name": f"Flow Org {suffix}", "slug": f"flow-org-{suffix}"})
    org_id = org_res.json()["id"]
    
    # 2. Setup Service
    svc_res = httpx.post(f"{BASE_URL}/services/", json={"name": "Flow Service", "organization_id": org_id})
    service_id = svc_res.json()["id"]
    
    # 3. Setup Specs
    # V1: Has POST /users
    spec_v1 = {
        "openapi": "3.0.0",
        "paths": {
            "/users": {
                "get": {},
                "post": {}
            }
        }
    }
    s1_res = httpx.post(f"{BASE_URL}/services/{service_id}/specs/", json={"version_label": "v1.0", "raw_spec": spec_v1})
    s1_id = s1_res.json()["id"]
    
    # V2: Removed POST /users (Breaking)
    spec_v2 = {
        "openapi": "3.0.0",
        "paths": {
            "/users": {
                "get": {}
            }
        }
    }
    s2_res = httpx.post(f"{BASE_URL}/services/{service_id}/specs/", json={"version_label": "v2.0", "raw_spec": spec_v2})
    s2_id = s2_res.json()["id"]
    
    # 4. Setup Consumer & Dependency
    cons_res = httpx.post(f"{BASE_URL}/consumers/", json={"name": "Flow Consumer", "organization_id": org_id})
    consumer_id = cons_res.json()["id"]
    
    # Consumer depends on the endpoint that will be broken (POST /users)
    httpx.post(f"{BASE_URL}/consumers/{consumer_id}/dependencies/", json={
        "service_id": service_id,
        "http_method": "POST",
        "path": "/users"
    })
    
    # 5. Trigger Analysis
    print("Triggering Analysis...")
    run_res = httpx.post(f"{BASE_URL}/analysis/runs/", json={
        "service_id": service_id,
        "old_spec_id": s1_id,
        "new_spec_id": s2_id
    })
    
    if run_res.status_code != 200:
        print(f"FAILED to trigger analysis: {run_res.text}")
        return
        
    run = run_res.json()
    print(f"Analysis Run ID: {run['id']}, Initial Status: {run['status']}")
    
    # Poll for completion
    print("Waiting for analysis to complete...")
    for _ in range(10): # retry 10 times
        time.sleep(1)
        status_res = httpx.get(f"{BASE_URL}/analysis/runs/{run['id']}")
        run = status_res.json()
        if run['status'] in ['SUCCESS', 'FAILED']:
            print(f"Analysis Finished. Status: {run['status']}")
            break
    
    if run['status'] != 'SUCCESS':
        print(f"ERROR: Analysis did not succeed. Status: {run['status']}")
        return

    # 6. Verify Results
    
    # Check Changes
    changes_res = httpx.get(f"{BASE_URL}/analysis/changes/?service_id={service_id}&new_spec_id={s2_id}")
    changes = changes_res.json()
    print(f"Found {len(changes)} changes.")
    
    breaking_change = next((c for c in changes if c['change_type'] == 'BREAKING' and c['http_method'] == 'POST'), None)
    if breaking_change:
        print("SUCCESS: Detected BREAKING change (POST /users removed).")
    else:
        print("ERROR: Did not detect breaking change.")
        
    # Check Impacts
    impacts_res = httpx.get(f"{BASE_URL}/analysis/impacts/?api_change_id={breaking_change['id'] if breaking_change else ''}")
    impacts = impacts_res.json()
    print(f"Found {len(impacts)} impacts.")
    
    if any(i['consumer_id'] == consumer_id for i in impacts):
        print("SUCCESS: Consumer marked as impacted.")
    else:
        print(f"ERROR: Consumer {consumer_id} not found in impacts.")

if __name__ == "__main__":
    test_analysis_flow()
