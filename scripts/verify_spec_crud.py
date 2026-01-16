import httpx
import uuid
import sys

BASE_URL = "http://127.0.0.1:8000/ruptrapi/v1"

def test_spec_crud():
    # 1. Create Org
    suffix = str(uuid.uuid4())[:8]
    org_slug = f"spec-test-org-{suffix}"
    print(f"Creating Org: {org_slug}")
    res = httpx.post(f"{BASE_URL}/organizations/", json={"name": f"Spec Test Org {suffix}", "slug": org_slug})
    if res.status_code != 200:
        print(f"Failed to create org: {res.text}")
        return
    org_id = res.json()["id"]

    # 2. Create Service
    print("Creating Service...")
    res = httpx.post(f"{BASE_URL}/services/", json={
        "name": "Spec Service",
        "description": "For testing specs",
        "base_path": "/api/v1/specs",
        "organization_id": org_id
    })
    if res.status_code != 200:
        print(f"Failed to create service: {res.text}")
        return
    service_id = res.json()["id"]

    # 3. Upload Spec
    print("Uploading Spec v1...")
    spec_v1 = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {}
    }
    res = httpx.post(f"{BASE_URL}/services/{service_id}/specs/", json={
        "version_label": "v1.0",
        "raw_spec": spec_v1
    })
    if res.status_code != 200:
        print(f"Failed to upload spec: {res.text}")
        return
    print("Spec v1 uploaded.")

    # 4. Upload Duplicate Spec
    print("Uploading Duplicate Spec (should fail)...")
    res = httpx.post(f"{BASE_URL}/services/{service_id}/specs/", json={
        "version_label": "v1.0-dup",
        "raw_spec": spec_v1 # Same content
    })
    if res.status_code != 409:
        print(f"ERROR: Duplicate spec upload did not fail. Status: {res.status_code}")
    else:
        print("Duplicate spec check passed.")

    # 5. Upload New Spec
    print("Uploading Spec v2...")
    spec_v2 = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "2.0.0"},
        "paths": {"/ping": {}}
    }
    res = httpx.post(f"{BASE_URL}/services/{service_id}/specs/", json={
        "version_label": "v2.0",
        "raw_spec": spec_v2
    })
    if res.status_code != 200:
        print(f"Failed to upload spec v2: {res.text}")
    else:
        print("Spec v2 uploaded.")

    # 6. List Specs
    print("Listing Specs...")
    res = httpx.get(f"{BASE_URL}/services/{service_id}/specs/")
    specs = res.json()
    if len(specs) != 2:
        print(f"ERROR: Expected 2 specs, got {len(specs)}")
    else:
        print("SUCCESS: Listed 2 specs.")

if __name__ == "__main__":
    test_spec_crud()
