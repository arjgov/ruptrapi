import httpx
import yaml
import json
import uuid
import sys
import os
import random
import copy
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000/ruptrapi/v1"

def load_yaml_spec(filepath):
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def sanitize_spec(item):
    """Recursively convert datetime objects to string for JSON serialization"""
    from datetime import date, datetime
    if isinstance(item, dict):
        return {k: sanitize_spec(v) for k, v in item.items()}
    elif isinstance(item, list):
        return [sanitize_spec(i) for i in item]
    elif isinstance(item, (datetime, date)):
        return item.isoformat()
    return item

def setup_service(org_name, service_name):
    # 1. Create Org
    suffix = str(uuid.uuid4())[:8]
    org_slug = f"{org_name.lower().replace(' ', '-')}-{suffix}"
    print(f"Creating Org: {org_name} ({org_slug})")
    org_res = httpx.post(f"{BASE_URL}/organizations/", json={"name": f"{org_name} {suffix}", "slug": org_slug})
    if org_res.status_code != 200:
        print(f"Failed to create org: {org_res.text}")
        sys.exit(1)
    org_id = org_res.json()["id"]

    # 2. Create Service
    print(f"Creating Service: {service_name}")
    svc_res = httpx.post(f"{BASE_URL}/services/", json={"name": service_name, "organization_id": org_id})
    if svc_res.status_code != 200:
        print(f"Failed to create service: {svc_res.text}")
        sys.exit(1)
    return org_id, svc_res.json()["id"]

def setup_consumer_dependency(org_id, service_id, method, path):
    # 1. Create Consumer
    print(f"Creating Consumer for impact testing...")
    con_res = httpx.post(f"{BASE_URL}/consumers/", json={
        "name": "RealWorld Consumer",
        "organization_id": org_id
    })
    if con_res.status_code != 200:
        print(f"Failed to create consumer: {con_res.text}")
        return None
    consumer_id = con_res.json()["id"]

    # 2. Add Dependency
    print(f"Adding Dependency on {method} {path}...")
    dep_res = httpx.post(f"{BASE_URL}/consumers/{consumer_id}/dependencies/", json={
        "service_id": service_id,
        "http_method": method,
        "path": path,
        "organization_id": org_id
    })
    if dep_res.status_code != 200:
        print(f"Failed to create dependency: {dep_res.text}")
    return consumer_id

def upload_spec(service_id, version_label, spec_dict):
    print(f"Uploading Spec {version_label}...")
    payload = {
        "version_label": version_label,
        "raw_spec": spec_dict
    }
    # Note: Pydantic expects dict, httpx handles json serialization
    res = httpx.post(f"{BASE_URL}/services/{service_id}/specs/", json=payload, timeout=30.0)
    if res.status_code != 200:
        print(f"Failed to upload spec: {res.text}")
        sys.exit(1)
    spec_id = res.json()["id"]
    print(f"  -> Success: {spec_id}")
    return spec_id

def mutate_spec(spec_dict):
    """
    Creates a V2 spec by removing a random path (BREAKING change).
    Returns (mutated_spec, description_of_change)
    """
    v2_spec = copy.deepcopy(spec_dict)
    paths = list(v2_spec.get("paths", {}).keys())
    
    if not paths:
        print("Warning: Spec has no paths to mutate.")
        return v2_spec, "No change"
        
    # Deterministic mutation for reliable testing? Or random?
    # Let's pick the first one to be deterministic if we run same test twice.
    target_path = paths[0]
    
    # Remove it
    del v2_spec["paths"][target_path]
    return v2_spec, f"Removed path {target_path}"

def run_verification(spec_path):
    filename = Path(spec_path).name
    service_name = f"Test {filename}"
    
    print(f"\n=== Verifying {filename} ===")
    
    # 0. Load Spec
    print("Loading YAML...")
    try:
        spec_v1_raw = load_yaml_spec(spec_path)
        spec_v1 = sanitize_spec(spec_v1_raw)
    except Exception as e:
        print(f"Failed to parse YAML: {e}")
        return

    # 1. Setup
    org_id, service_id = setup_service("RealWorld Verify", service_name)
    
    # 2. Upload V1
    upload_spec(service_id, "v1.0", spec_v1)

    # 3. Create a Dependency to test Impact
    # We'll create a dependency on the first path we are about to delete
    paths = list(spec_v1.get("paths", {}).keys())
    if paths:
        target_path = paths[0]
        # Most real world specs have 'get' or 'post' for the first path
        method = "GET"
        if "get" not in spec_v1["paths"][target_path]:
            # Try to find any method
            for m in ["post", "put", "delete", "patch"]:
                if m in spec_v1["paths"][target_path]:
                    method = m.upper()
                    break
        setup_consumer_dependency(org_id, service_id, method, target_path)
    
    # 4. Create & Upload V2 (Mutated)
    spec_v2, mutation_desc = mutate_spec(spec_v1)
    print(f"Mutation Applied: {mutation_desc}")
    upload_spec(service_id, "v2.0", spec_v2)
    
    # 5. Trigger Analysis
    print("Triggering Analysis...")
    run_res = httpx.post(f"{BASE_URL}/analysis/runs/", json={"service_id": service_id}, timeout=10.0)
    if run_res.status_code != 200:
        print(f"Failed to trigger analysis: {run_res.text}")
        return
    
    run_id = run_res.json()["id"]
    print(f"Analysis Run ID: {run_id}")
    
    # 6. Poll for completion
    print("Waiting for completion...")
    final_status = "PENDING"
    for _ in range(30): # Wait up to 30s
        time.sleep(1)
        status_res = httpx.get(f"{BASE_URL}/analysis/runs/{run_id}")
        final_status = status_res.json()["status"]
        if final_status in ["SUCCESS", "FAILED"]:
            break
    
    print(f"Final Status: {final_status}")
    
    if final_status == "SUCCESS":
        # Check Changes
        changes_res = httpx.get(f"{BASE_URL}/analysis/changes/?analysis_run_id={run_id}")
        changes = changes_res.json()
        print(f"Found {len(changes)} changes.")
        
        # Verify we caught the detailed change
        breaking = [c for c in changes if c['severity'] == 'HIGH']
        if breaking:
            print("SUCCESS: Detected BREAKING changes.")
        
        # Check Impacts
        impacts_res = httpx.get(f"{BASE_URL}/analysis/impacts/?analysis_run_id={run_id}")
        impacts = impacts_res.json()
        print(f"Found {len(impacts)} impacted consumers.")
        for imp in impacts:
             print(f"  - Impacted Consumer ID: {imp['consumer_id']} (Risk: {imp['risk_level']})")
            
    else:
        print("ERROR: Analysis failed.")

if __name__ == "__main__":
    # If args provided, use them, else default to docker
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        # Default dict
        base_dir = Path(__file__).parent.parent / "backend/tests/openapi"
        files = [
            base_dir / "docker v1.yaml",
            # Add others if they exist
        ]
    
    for f in files:
        if os.path.exists(f):
            run_verification(f)
        else:
            print(f"File not found: {f}")
