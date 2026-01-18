import httpx
import uuid
import sys
import time

BASE_URL = "http://127.0.0.1:8000/ruptrapi/v1"

def test_auto_analysis():
    # 1. Setup Org & Service
    suffix = str(uuid.uuid4())[:8]
    print(f"Setting up test environment (Suffix: {suffix})...")
    
    org_res = httpx.post(f"{BASE_URL}/organizations/", json={"name": f"Auto Org {suffix}", "slug": f"auto-org-{suffix}"})
    org_id = org_res.json()["id"]
    
    svc_res = httpx.post(f"{BASE_URL}/services/", json={"name": "Auto Service", "organization_id": org_id})
    service_id = svc_res.json()["id"]
    
    # 2. Upload Specs (V1 then V2)
    # V1
    spec_v1 = {
        "openapi": "3.0.0",
        "paths": {"/test": {"get": {}}}
    }
    s1_res = httpx.post(f"{BASE_URL}/services/{service_id}/specs/", json={"version_label": "v1.0", "raw_spec": spec_v1})
    if s1_res.status_code != 200:
        print(f"Failed to upload V1: {s1_res.text}")
        return
    print("Uploaded V1")
    time.sleep(1) # Ensure timestamp diff
    
    # V2 (Breaking: remove /test)
    spec_v2 = {
        "openapi": "3.0.0",
        "paths": {}
    }
    s2_res = httpx.post(f"{BASE_URL}/services/{service_id}/specs/", json={"version_label": "v2.0", "raw_spec": spec_v2})
    if s2_res.status_code != 200:
        print(f"Failed to upload V2: {s2_res.text}")
        return
    print("Uploaded V2")
    
    # 3. Trigger Analysis WITHOUT spec IDs
    print("Triggering Analysis (Auto-Select)...")
    run_res = httpx.post(f"{BASE_URL}/analysis/runs/", json={
        "service_id": service_id
        # No old_spec_id or new_spec_id
    })
    
    if run_res.status_code != 200:
        print(f"FAILED to trigger analysis: {run_res.text}")
        return
        
    run = run_res.json()
    print(f"Analysis Run ID: {run['id']}, Status: {run['status']}")
    
    # Verify it picked the right IDs
    chosen_old = run['old_spec_id']
    chosen_new = run['new_spec_id']
    
    # V2 (newest) should be new_spec_id, V1 (older) should be old_spec_id
    # Note: Logic was `latest_specs = order_by(created_at.desc()).limit(2)`
    # latest_specs[0] is V2, latest_specs[1] is V1.
    # Code: new_id = latest_specs[0].id, old_id = latest_specs[1].id
    
    if chosen_new == s2_res.json()['id'] and chosen_old == s1_res.json()['id']:
        print("SUCCESS: Correctly selected latest V2 as new and V1 as old.")
    else:
        print(f"ERROR: ID Mismatch.\nExpected New: {s2_res.json()['id']}, Got: {chosen_new}\nExpected Old: {s1_res.json()['id']}, Got: {chosen_old}")
        return

    # Check execution
    print("Waiting for completion...")
    for _ in range(10):
        time.sleep(1)
        status = httpx.get(f"{BASE_URL}/analysis/runs/{run['id']}").json()['status']
        if status in ['SUCCESS', 'FAILED']:
            print(f"Final Status: {status}")
            break
            
    if status == 'SUCCESS':
        print("Test PASSED.")
    else:
        print("Test FAILED (Execution failed).")

if __name__ == "__main__":
    test_auto_analysis()
